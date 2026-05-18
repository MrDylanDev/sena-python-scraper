"""Composition root: read offers, dedup, send emails, log envios.

Usage:
    python send_applications.py             # send for real
    python send_applications.py --dry-run   # preview only, no SMTP
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make `src/` layout importable without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sena_scraper.config import load_settings
from sena_scraper.envio_storage import (
    EnvioRecord,
    append_record,
    build_dedup_set,
    load_sent_emails,
)
from sena_scraper.errors import ConfigError, MailerError
from sena_scraper.imap_dedupe import (
    close_imap,
    connect_imap,
    fetch_sent_recipients,
    find_sent_folder,
)
from sena_scraper.mailer import (
    close_smtp,
    connect_smtp,
    is_valid_email,
    normalize_email,
    render_body,
    render_subject,
    send_email,
    time_greeting,
)

log = logging.getLogger("send_applications")


def load_offers(path: Path) -> list[dict]:
    """Read offers from the JSONL file produced by the scraper."""
    if not path.exists():
        return []
    offers: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if raw:
                offers.append(json.loads(raw))
    return offers


def _now_iso() -> str:
    """UTC ISO 8601 timestamp with seconds precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send ADSO sponsorship application emails."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    args = parser.parse_args()
    dry = args.dry_run

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = load_settings()
    if not settings.gmail_user or not settings.gmail_app_password:
        raise ConfigError("GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env")

    if len(settings.gmail_app_password) != 16:
        log.warning(
            "GMAIL_APP_PASSWORD is not 16 chars — verify it is a valid App Password"
        )

    offers = load_offers(Path("data/ofertas_adso_antioquia.jsonl"))
    log.info("Loaded %d offers", len(offers))

    # Build dedup set from BOTH sources (REQ-1)
    local_emails = load_sent_emails(settings.envios_path)
    log.info("Local sent log has %d unique emails", len(local_emails))

    imap = connect_imap(settings)
    try:
        sent_folder = find_sent_folder(imap)
        log.info("Detected Sent folder: %s", sent_folder)
        imap_emails = fetch_sent_recipients(
            imap, sent_folder, settings.imap_lookback_days
        )
        log.info(
            "IMAP scan found %d unique recipients (last %d days)",
            len(imap_emails),
            settings.imap_lookback_days,
        )
    finally:
        close_imap(imap)

    dedup = build_dedup_set(local_emails, imap_emails)

    # SMTP connection (skip in dry-run)
    smtp = None if dry else connect_smtp(settings)

    sent = skipped = failed = invalid = 0
    try:
        for offer in offers:
            raw_correo = (offer.get("correo") or "").strip().lower()
            correo = normalize_email(raw_correo)
            if correo != raw_correo:
                log.info("Auto-corrected email: %r → %r", raw_correo, correo)
            id_sol = offer.get("id_solicitud", "")
            empresa = offer.get("empresa", "")

            if not is_valid_email(correo):
                if not dry:
                    rec = EnvioRecord(
                        id_sol, empresa, correo, "", "invalid_email",
                        "regex mismatch", _now_iso(),
                    )
                    append_record(settings.envios_path, rec)
                invalid += 1
                log.warning("Invalid email for %s: %r", empresa, correo)
                continue

            if correo in dedup:
                skipped += 1
                log.info("Skip %s (%s) — already in dedup set", correo, empresa)
                continue

            saludo = time_greeting()
            subject = render_subject()
            body = render_body(saludo)

            if dry:
                print(f"\n[DRY-RUN] To: {correo}")
                print(f"  Subject: {subject}")
                print("  Body:")
                for line in body.splitlines():
                    print(f"    {line}")
                continue

            try:
                send_email(smtp, settings.gmail_user, correo, subject, body)
                rec = EnvioRecord(
                    id_sol, empresa, correo, subject, "sent", "", _now_iso(),
                )
                append_record(settings.envios_path, rec)
                dedup.add(correo)
                sent += 1
                log.info("✅ Sent %s (%s)", correo, empresa)
            except Exception as exc:  # noqa: BLE001
                rec = EnvioRecord(
                    id_sol, empresa, correo, subject, "failed",
                    str(exc)[:200], _now_iso(),
                )
                append_record(settings.envios_path, rec)
                failed += 1
                log.warning("❌ Failed %s (%s): %s", correo, empresa, exc)

            time.sleep(
                random.uniform(settings.inter_send_min_s, settings.inter_send_max_s)
            )
    finally:
        if smtp:
            close_smtp(smtp)

    log.info(
        "Done. Sent: %d | Skipped: %d | Failed: %d | Invalid: %d",
        sent, skipped, failed, invalid,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

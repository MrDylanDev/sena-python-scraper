"""Persistence of send attempts to data/envios.jsonl."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnvioRecord:
    """One row of envios.jsonl. Matches REQ-7 schema."""

    id_solicitud: str
    empresa: str
    correo: str  # lowercased before storage
    subject: str
    status: str  # "sent" | "failed" | "invalid_email"
    error: str  # "" when sent
    timestamp: str  # ISO 8601 UTC

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def load_sent_records(path: Path) -> list[EnvioRecord]:
    """Read all records from envios.jsonl. Skips and logs malformed lines.
    Returns [] if the file does not exist.
    """
    if not path.exists():
        return []

    records: list[EnvioRecord] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
                records.append(EnvioRecord(**row))
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                log.warning("Skipping malformed line %d in %s: %s", lineno, path, exc)
    return records


def load_sent_emails(path: Path) -> set[str]:
    """Return the set of lowercased emails for records whose status is 'sent'."""
    return {r.correo.lower() for r in load_sent_records(path) if r.status == "sent"}


def append_record(path: Path, record: EnvioRecord) -> None:
    """Append one record as a JSON line with ensure_ascii=False.
    Creates parent dirs if missing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record.to_dict(), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.write("\n")


def build_dedup_set(local_emails: set[str], imap_emails: set[str]) -> set[str]:
    """Return the union of both sets, normalized lowercase. Pure function."""
    return {e.lower() for e in local_emails} | {e.lower() for e in imap_emails}

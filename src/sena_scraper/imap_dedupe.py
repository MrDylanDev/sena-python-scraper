"""Read Gmail's Sent folder via IMAP to find recipients we already wrote to."""

from __future__ import annotations

import email.utils
import imaplib
import logging
import re
from datetime import datetime, timedelta, timezone

from .config import Settings
from .errors import MailerError

log = logging.getLogger(__name__)

KNOWN_SENT_FOLDERS = [
    "[Gmail]/Sent Mail",
    "[Gmail]/Enviados",
]


def connect_imap(settings: Settings) -> imaplib.IMAP4_SSL:
    """Open and authenticate an IMAP connection to imap.gmail.com:993.

    Raises:
        MailerError: if connection or authentication fails.
    """
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        imap.login(settings.gmail_user, settings.gmail_app_password)
        return imap
    except (imaplib.IMAP4.error, OSError) as exc:
        raise MailerError(f"IMAP connection/auth failed: {exc}") from exc


def find_sent_folder(imap: imaplib.IMAP4_SSL) -> str:
    """Auto-detect the Gmail Sent folder name.

    Strategy:
      1. LIST all folders — find one with \\Sent SPECIAL-USE attribute.
      2. Fallback: try KNOWN_SENT_FOLDERS in order via SELECT.
      3. Raise MailerError if none found.
    """
    # Strategy 1: parse LIST for \Sent attribute
    status, data = imap.list()
    if status == "OK" and data:
        for item in data:
            if item is None:
                continue
            line = item.decode("utf-8", errors="replace") if isinstance(item, bytes) else str(item)
            if "\\Sent" in line:
                # Extract folder name from LIST response: (attrs) "delim" "name"
                match = re.search(r'"([^"]+)"\s*$', line)
                if match:
                    return match.group(1)
                # Try unquoted format
                parts = line.rsplit(" ", 1)
                if len(parts) == 2:
                    return parts[1].strip('"')

    # Strategy 2: fallback to known folder names
    for folder in KNOWN_SENT_FOLDERS:
        status, _ = imap.select(f'"{folder}"', readonly=True)
        if status == "OK":
            return folder

    raise MailerError(
        "Could not detect Gmail Sent folder. "
        "Check account language or IMAP settings."
    )


def fetch_sent_recipients(
    imap: imaplib.IMAP4_SSL,
    folder: str,
    days: int,
) -> set[str]:
    """Fetch lowercased recipient emails from messages sent in the last `days`.

    Empty set on no matches. Logs but does not raise on per-message
    parse errors.
    """
    imap.select(f'"{folder}"', readonly=True)

    since_date = datetime.now(timezone.utc) - timedelta(days=days)
    date_str = since_date.strftime("%d-%b-%Y")

    status, uid_data = imap.uid("SEARCH", None, f"SINCE {date_str}")
    if status != "OK" or not uid_data or not uid_data[0]:
        return set()

    uids = uid_data[0].split()
    recipients: set[str] = set()

    # Fetch in batches of 50
    batch_size = 50
    for i in range(0, len(uids), batch_size):
        batch = b",".join(uids[i : i + batch_size])
        status, msg_data = imap.uid(
            "FETCH", batch, "(BODY.PEEK[HEADER.FIELDS (TO)])"
        )
        if status != "OK" or not msg_data:
            continue

        for item in msg_data:
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            try:
                header = item[1].decode("utf-8", errors="replace")
                pairs = email.utils.getaddresses([header.replace("To:", "").strip()])
                for _, addr in pairs:
                    if addr:
                        recipients.add(addr.lower())
            except Exception as exc:  # noqa: BLE001
                log.warning("IMAP parse error (skipping message): %s", exc)

    return recipients


def close_imap(imap: imaplib.IMAP4_SSL) -> None:
    """Best-effort IMAP logout."""
    try:
        imap.logout()
    except Exception as exc:  # noqa: BLE001
        log.warning("IMAP close error (non-fatal): %s", exc)

"""Gmail SMTP send + email rendering.

Pure rendering functions are stateless; SMTP functions take an open
connection so the caller controls connection lifecycle.
"""

from __future__ import annotations

import logging
import re
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from .config import Settings
from .errors import MailerError

log = logging.getLogger(__name__)

SUBJECT_TEMPLATE: str = "Postulación a oferta ADSO - SENA"

BODY_TEMPLATE: str = """\
{{saludo}}

Mi nombre es Dylan Ospina, aprendiz del programa ADSO (Análisis y
Desarrollo de Software) del SENA, actualmente en etapa lectiva.
Vi su oferta en el SGVA y me interesa postularme.

Me gustaría orientar mi formación hacia las herramientas y
metodologías que su equipo utiliza, para aportar con efectividad
desde el primer día de mi etapa práctica.

Quedo atento a una breve entrevista o charla técnica. Muchas
gracias por su atención.

Cordialmente,
Dylan Ospina
Cel: 3233805088
"""

EMAIL_REGEX: re.Pattern[str] = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

COLOMBIA_TZ = timezone(timedelta(hours=-5))


# --- Pure functions ---


def time_greeting(now: datetime | None = None) -> str:
    """Return the greeting matching Colombian local time.

    Args:
        now: timezone-aware datetime. If None, uses datetime.now in UTC-5.

    Returns:
        "Buenos días." | "Buenas tardes." | "Buenas noches."
    """
    if now is None:
        now = datetime.now(COLOMBIA_TZ)
    else:
        now = now.astimezone(COLOMBIA_TZ)

    hour = now.hour
    if 5 <= hour <= 11:
        return "Buenos días."
    if 12 <= hour <= 18:
        return "Buenas tardes."
    return "Buenas noches."


def is_valid_email(email: str) -> bool:
    """Lightweight regex check for `something@host.tld` shape.

    Trims whitespace before checking. NOT full RFC 5322.
    """
    return bool(EMAIL_REGEX.match(email.strip()))


def normalize_email(email: str) -> str:
    """Apply common typo corrections to an email address.

    Currently fixes:
        - Trims surrounding whitespace.
        - Replaces ``,`` with ``.`` ONLY in the domain part (after the
          last ``@``). A comma in the local part is left untouched
          because it is genuinely invalid per RFC 5321 — letting it
          through would mask a real error.

    Returns the (possibly corrected) email. Does NOT validate; the caller
    should pass the result through ``is_valid_email`` afterwards.
    """
    cleaned = email.strip()
    if cleaned.count("@") != 1:
        return cleaned
    local, _, domain = cleaned.rpartition("@")
    domain = domain.replace(",", ".")
    return f"{local}@{domain}"


def render_subject() -> str:
    """Return the constant SUBJECT_TEMPLATE."""
    return SUBJECT_TEMPLATE


def render_body(saludo: str) -> str:
    """Substitute {{saludo}} in BODY_TEMPLATE."""
    return BODY_TEMPLATE.replace("{{saludo}}", saludo)


# --- SMTP I/O ---


def connect_smtp(settings: Settings) -> smtplib.SMTP_SSL:
    """Open and authenticate an SMTP_SSL connection to smtp.gmail.com:465.

    Raises:
        MailerError: if connection or authentication fails.
    """
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(settings.gmail_user, settings.gmail_app_password)
        return smtp
    except (smtplib.SMTPException, OSError) as exc:
        raise MailerError(f"SMTP connection/auth failed: {exc}") from exc


def send_email(
    smtp: smtplib.SMTP_SSL,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> None:
    """Send a plain-text email via the open SMTP connection."""
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    smtp.send_message(msg)


def close_smtp(smtp: smtplib.SMTP_SSL) -> None:
    """Best-effort SMTP close. Swallows errors, logs warnings."""
    try:
        smtp.quit()
    except Exception as exc:  # noqa: BLE001
        log.warning("SMTP close error (non-fatal): %s", exc)

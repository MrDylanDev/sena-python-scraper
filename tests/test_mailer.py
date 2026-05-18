"""Unit tests for sena_scraper.mailer — greeting, validation, rendering."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sena_scraper.mailer import (
    BODY_TEMPLATE,
    SUBJECT_TEMPLATE,
    is_valid_email,
    render_body,
    render_subject,
    time_greeting,
)

COLOMBIA_TZ = timezone(timedelta(hours=-5))


# --- time_greeting ---


def test_time_greeting_morning():
    """8:00 COL → Buenos días."""
    dt = datetime(2026, 5, 18, 8, 0, tzinfo=COLOMBIA_TZ)
    assert time_greeting(dt) == "Buenos días."


def test_time_greeting_afternoon():
    """14:00 COL → Buenas tardes."""
    dt = datetime(2026, 5, 18, 14, 0, tzinfo=COLOMBIA_TZ)
    assert time_greeting(dt) == "Buenas tardes."


def test_time_greeting_night():
    """22:00 COL → Buenas noches."""
    dt = datetime(2026, 5, 18, 22, 0, tzinfo=COLOMBIA_TZ)
    assert time_greeting(dt) == "Buenas noches."


def test_time_greeting_boundary_5am():
    """5:00 sharp → Buenos días."""
    dt = datetime(2026, 5, 18, 5, 0, tzinfo=COLOMBIA_TZ)
    assert time_greeting(dt) == "Buenos días."


def test_time_greeting_boundary_12pm():
    """12:00 sharp → Buenas tardes."""
    dt = datetime(2026, 5, 18, 12, 0, tzinfo=COLOMBIA_TZ)
    assert time_greeting(dt) == "Buenas tardes."


def test_time_greeting_boundary_7pm():
    """19:00 sharp → Buenas noches."""
    dt = datetime(2026, 5, 18, 19, 0, tzinfo=COLOMBIA_TZ)
    assert time_greeting(dt) == "Buenas noches."


# --- is_valid_email ---


def test_is_valid_email_simple():
    """Standard email passes."""
    assert is_valid_email("user@example.com") is True


def test_is_valid_email_invalid_comma():
    """Comma instead of dot fails (REQ-6 case)."""
    assert is_valid_email("rhenus,com") is False


def test_is_valid_email_no_at():
    """Missing @ fails."""
    assert is_valid_email("userexample.com") is False


def test_is_valid_email_trims():
    """Surrounding whitespace is trimmed before check."""
    assert is_valid_email("  user@example.com  ") is True


# --- render_* ---


def test_render_subject_constant():
    """Subject is the frozen constant."""
    assert render_subject() == SUBJECT_TEMPLATE


def test_render_body_substitutes_saludo():
    """Body replaces {{saludo}} with the provided greeting."""
    body = render_body("Buenos días.")
    assert body.startswith("Buenos días.\n")
    assert "{{saludo}}" not in body
    assert "Dylan Ospina" in body


# --- normalize_email ---


def test_normalize_email_comma_in_domain():
    """Comma in the domain is corrected to dot."""
    from sena_scraper.mailer import normalize_email
    assert normalize_email("user@host,com") == "user@host.com"
    assert normalize_email("a.b@example,co") == "a.b@example.co"


def test_normalize_email_unchanged_local_comma():
    """Comma in the local part is preserved (it stays invalid for is_valid_email)."""
    from sena_scraper.mailer import normalize_email
    assert normalize_email("a,b@host.com") == "a,b@host.com"


def test_normalize_email_no_change_needed():
    """Well-formed email passes through unchanged."""
    from sena_scraper.mailer import normalize_email
    assert normalize_email("user@host.com") == "user@host.com"


def test_normalize_email_strips_whitespace():
    """Surrounding whitespace is trimmed."""
    from sena_scraper.mailer import normalize_email
    assert normalize_email("  user@host,com  ") == "user@host.com"


def test_normalize_email_real_world_rhenus():
    """Regression: the actual SENA-extracted typo julieth.solano@rhenus,com."""
    from sena_scraper.mailer import normalize_email
    assert normalize_email("julieth.solano@rhenus,com") == "julieth.solano@rhenus.com"

"""Typed exceptions for the SENA scraper.

Hierarchy:
    SenaScraperError                 (base)
    ├── ConfigError                  (missing env vars, bad config)
    ├── LoginFailed                  (auth attempt did not reach dashboard)
    ├── NavigationFailed             (could not reach a target page/state)
    ├── ExtractionFailed             (modal data unreadable for one offer)
    └── MailerError                  (SMTP/IMAP connection or auth failure)
"""

from __future__ import annotations


class SenaScraperError(Exception):
    """Base class for all scraper-specific errors."""


class ConfigError(SenaScraperError):
    """Configuration is invalid or required values are missing."""


class LoginFailed(SenaScraperError):
    """Authentication did not complete successfully."""


class NavigationFailed(SenaScraperError):
    """Could not navigate to or render the expected page/state."""


class ExtractionFailed(SenaScraperError):
    """Failed to extract data for a single offer; safe to skip and continue.

    Attributes:
        id_solicitud: the solicitud id whose extraction failed (if known).
        reason: a short human-readable cause.
    """

    def __init__(self, reason: str, id_solicitud: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.id_solicitud = id_solicitud


class MailerError(SenaScraperError):
    """SMTP/IMAP connection or authentication failure."""
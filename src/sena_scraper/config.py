"""Configuration loaded from environment variables.

Settings is a frozen dataclass so it cannot be mutated after construction.
load_settings() reads from .env via python-dotenv and validates required keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .errors import ConfigError


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the SENA scraper.

    Required values come from environment variables; defaults are tuned
    for the v1 scope (Antioquia, ADSO program).
    """

    # Required (from .env)
    usuario: str
    password: str
    documento: str

    # SENA portal
    login_url: str = "https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx"
    dashboard_url: str = (
        "https://caprendizaje.sena.edu.co/sgva/Aprendices/Index"
    )
    solicitudes_url: str = (
        "https://caprendizaje.sena.edu.co/sgva/Aprendices/Solicitudes/"
    )

    # Filters (v1 hardcoded; future configurable)
    departamento_value: str = "5"  # ANTIOQUIA
    programa_substring: str = "ANALISIS Y DESARROLLO DE SOFTWARE"

    # Output
    output_path: Path = field(
        default_factory=lambda: Path("data/ofertas_adso_antioquia.jsonl")
    )

    # Browser
    headless: bool = False

    # Timeouts (seconds)
    page_load_timeout: int = 60
    modal_timeout: int = 30

    # Human-pacing throttle between modals (seconds)
    inter_modal_min_s: float = 2.0
    inter_modal_max_s: float = 4.0

    # Logging
    log_level: str = "INFO"

    # Gmail (mailer)
    gmail_user: str = ""
    gmail_app_password: str = ""

    # Pacing (mailer)
    inter_send_min_s: float = 30.0
    inter_send_max_s: float = 60.0

    # IMAP dedup
    imap_lookback_days: int = 60

    # Envios output
    envios_path: Path = field(
        default_factory=lambda: Path("data/envios.jsonl")
    )


def load_settings(env_path: Path | None = None) -> Settings:
    """Load settings from a .env file and the process environment.

    Args:
        env_path: optional explicit path to a .env file. If None, dotenv
            searches the current working directory and parents.

    Raises:
        ConfigError: when any required variable is missing or empty.
    """
    if env_path is not None:
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        load_dotenv(override=False)

    usuario = os.getenv("SENA_USUARIO", "").strip()
    password = os.getenv("SENA_PASSWORD", "")
    documento = os.getenv("SENA_TIPO_DOCUMENTO", "").strip()

    missing = [
        name
        for name, value in [
            ("SENA_USUARIO", usuario),
            ("SENA_PASSWORD", password),
            ("SENA_TIPO_DOCUMENTO", documento),
        ]
        if not value
    ]
    if missing:
        raise ConfigError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in the values."
        )

    return Settings(
        usuario=usuario,
        password=password,
        documento=documento,
        gmail_user=os.getenv("GMAIL_USER", "").strip(),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
    )

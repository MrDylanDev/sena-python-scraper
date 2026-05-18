"""Smoke tests — validate imports, config validation, and storage roundtrip."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_all_modules_import():
    """Every sena_scraper submodule imports without error."""
    import sena_scraper
    import sena_scraper.config
    import sena_scraper.constants
    import sena_scraper.errors
    import sena_scraper.extraction
    import sena_scraper.login
    import sena_scraper.navigation
    import sena_scraper.overlays
    import sena_scraper.session
    import sena_scraper.storage

    assert sena_scraper.__version__


def test_load_settings_raises_on_missing_env(monkeypatch):
    """load_settings() raises ConfigError when required vars are absent."""
    from sena_scraper.config import load_settings
    from sena_scraper.errors import ConfigError

    monkeypatch.delenv("SENA_USUARIO", raising=False)
    monkeypatch.delenv("SENA_PASSWORD", raising=False)
    monkeypatch.delenv("SENA_TIPO_DOCUMENTO", raising=False)

    with pytest.raises(ConfigError, match="Missing required environment variables"):
        load_settings(env_path=Path("/dev/null"))


def test_storage_roundtrip(tmp_path):
    """append_offer writes a valid JSONL line; load_existing_ids reads it back."""
    from sena_scraper.extraction import Offer
    from sena_scraper.storage import append_offer, load_existing_ids

    jsonl = tmp_path / "test.jsonl"

    offer = Offer(
        id_solicitud="12345",
        empresa="Test Corp",
        correo="test@example.com",
        telefono="3001234567",
        programa="ANALISIS Y DESARROLLO DE SOFTWARE",
        departamento="ANTIOQUIA",
        ciudad="MEDELLIN",
        contacto="Juan Pérez",
        fecha_cierre="2026-06-01",
        fecha_extraccion="2026-05-18T00:00:00+00:00",
    )

    append_offer(jsonl, offer)

    ids = load_existing_ids(jsonl)
    assert "12345" in ids

    # Verify the line is valid JSON with all fields
    line = jsonl.read_text(encoding="utf-8").strip()
    row = json.loads(line)
    assert row["id_solicitud"] == "12345"
    assert row["empresa"] == "Test Corp"
    assert row["contacto"] == "Juan Pérez"  # ensure_ascii=False preserved

"""Unit tests for sena_scraper.envio_storage — persistence and dedup."""

from __future__ import annotations

import json

from sena_scraper.envio_storage import (
    EnvioRecord,
    append_record,
    build_dedup_set,
    load_sent_emails,
    load_sent_records,
)


def test_load_sent_emails_only_returns_status_sent(tmp_path):
    """Only records with status='sent' appear in the dedup set."""
    jsonl = tmp_path / "envios.jsonl"
    sent = EnvioRecord("1", "A", "a@b.com", "s", "sent", "", "2026-01-01T00:00:00+00:00")
    failed = EnvioRecord("2", "B", "c@d.com", "s", "failed", "err", "2026-01-01T00:00:00+00:00")
    append_record(jsonl, sent)
    append_record(jsonl, failed)

    emails = load_sent_emails(jsonl)
    assert "a@b.com" in emails
    assert "c@d.com" not in emails


def test_load_sent_emails_lowercases(tmp_path):
    """Emails are lowercased in the dedup set."""
    jsonl = tmp_path / "envios.jsonl"
    rec = EnvioRecord("1", "A", "User@Example.COM", "s", "sent", "", "2026-01-01T00:00:00+00:00")
    append_record(jsonl, rec)

    emails = load_sent_emails(jsonl)
    assert "user@example.com" in emails


def test_append_record_roundtrip(tmp_path):
    """A record written with append_record can be read back."""
    jsonl = tmp_path / "envios.jsonl"
    rec = EnvioRecord("99", "Corp", "x@y.co", "subj", "sent", "", "2026-05-18T12:00:00+00:00")
    append_record(jsonl, rec)

    records = load_sent_records(jsonl)
    assert len(records) == 1
    assert records[0].id_solicitud == "99"
    assert records[0].correo == "x@y.co"


def test_load_sent_records_skips_malformed_lines(tmp_path):
    """Malformed JSON lines are skipped without crashing."""
    jsonl = tmp_path / "envios.jsonl"
    good = json.dumps(EnvioRecord("1", "A", "a@b.com", "s", "sent", "", "t").to_dict())
    jsonl.write_text(f"not json at all\n{good}\n", encoding="utf-8")

    records = load_sent_records(jsonl)
    assert len(records) == 1
    assert records[0].id_solicitud == "1"


def test_build_dedup_set_union_lowercase():
    """Union of both sets, all lowercased."""
    local = {"A@B.com", "c@d.com"}
    imap = {"E@F.COM", "c@d.com"}

    result = build_dedup_set(local, imap)
    assert result == {"a@b.com", "c@d.com", "e@f.com"}

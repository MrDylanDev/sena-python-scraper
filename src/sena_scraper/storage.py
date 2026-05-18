"""JSONL-backed idempotent storage for extracted offers.

We use append-only JSONL so a mid-run crash keeps progress. Idempotency
is enforced by the caller: load_existing_ids() at startup, then skip any
id_solicitud that already exists before opening its modal.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .extraction import Offer

log = logging.getLogger(__name__)


def load_existing_ids(path: Path) -> set[str]:
    """Return the set of id_solicitud values already in the JSONL file.

    Missing or empty file → empty set. Malformed lines are skipped with a
    warning (we never crash on partial-write damage).
    """
    if not path.exists():
        return set()

    ids: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                log.warning(
                    "Skipping malformed line %d in %s (not valid JSON)", lineno, path
                )
                continue
            id_sol = row.get("id_solicitud")
            if isinstance(id_sol, str) and id_sol:
                ids.add(id_sol)
    log.info("Loaded %d existing id_solicitud(s) from %s", len(ids), path)
    return ids


def append_offer(path: Path, offer: Offer) -> None:
    """Append a single Offer as one JSONL line. Creates parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(offer.to_dict(), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.write("\n")

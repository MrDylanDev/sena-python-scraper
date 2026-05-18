"""SENA ADSO Antioquia offer extractor — composition root.

Usage:
    python main.py

Requires a populated .env file (see .env.example).
"""

from __future__ import annotations

import logging
import random
import sys
import time
from pathlib import Path

# Make `src/` layout importable without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sena_scraper.config import load_settings
from sena_scraper.errors import ExtractionFailed, LoginFailed, NavigationFailed
from sena_scraper.extraction import (
    Offer,
    close_modal,
    find_card_button,
    open_modal,
    read_all_cards,
    read_modal,
)
from sena_scraper.navigation import (
    filter_departamento,
    goto_next_page,
    goto_solicitudes,
    wait_results_or_empty,
)
from sena_scraper.session import build_driver, close_driver
from sena_scraper.storage import append_offer, load_existing_ids

log = logging.getLogger("sena_scraper")

DEBUG_DIR = Path("data/debug")


def _screenshot(driver, name: str) -> None:
    """Save a checkpoint screenshot to data/debug/. Best-effort."""
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        path = DEBUG_DIR / name
        driver.save_screenshot(str(path))
        log.info("📸 Screenshot saved: %s", path)
    except Exception as exc:  # noqa: BLE001
        log.warning("Screenshot failed (%s): %s", name, exc)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = load_settings()
    existing_ids = load_existing_ids(settings.output_path)
    log.info("Starting extraction (known offers: %d)", len(existing_ids))

    driver = build_driver(settings)
    try:
        login_and_extract(driver, settings, existing_ids)
    except (LoginFailed, NavigationFailed) as exc:
        log.error("Fatal: %s", exc)
        _screenshot(driver, "04_estado_final.png")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected error: %s", exc)
        _screenshot(driver, "04_estado_final.png")
        raise
    else:
        _screenshot(driver, "04_estado_final.png")
    finally:
        close_driver(driver)


def login_and_extract(driver, settings, existing_ids: set[str]) -> None:
    from sena_scraper.login import login_aprendiz

    login_aprendiz(driver, settings)
    _screenshot(driver, "01_post_login.png")
    goto_solicitudes(driver, settings)
    filter_departamento(driver, settings)
    _screenshot(driver, "02_post_filtro.png")

    if not wait_results_or_empty(driver, settings):
        log.info("No offers found for department=%s", settings.departamento_value)
        return

    new_count = 0
    skipped = 0
    failed = 0
    page = 1
    first_modal_captured = False

    while True:
        log.info("Processing page %d", page)
        cards = read_all_cards(driver)
        log.info("Page %d: %d card(s) in snapshot", page, len(cards))

        for card in cards:
            if card.id_solicitud in existing_ids:
                skipped += 1
                continue

            btn = find_card_button(driver, card.id_solicitud)
            if btn is None:
                log.warning(
                    "Card %s vanished from DOM before click; skipping",
                    card.id_solicitud,
                )
                failed += 1
                continue

            try:
                open_modal(driver, btn, settings, card.id_solicitud)
                if not first_modal_captured:
                    _screenshot(driver, "03_modal_abierto.png")
                    first_modal_captured = True
                modal = read_modal(driver, card.id_solicitud)
            except ExtractionFailed as exc:
                log.warning("Extraction failed for %s: %s", card.id_solicitud, exc)
                close_modal(driver)
                failed += 1
                continue

            close_modal(driver)

            # Filter: only ADSO program
            if settings.programa_substring.upper() not in modal.programa.upper():
                skipped += 1
                existing_ids.add(card.id_solicitud)  # don't re-open next run
                continue

            offer = Offer.merge(card, modal)
            append_offer(settings.output_path, offer)
            existing_ids.add(card.id_solicitud)
            new_count += 1
            log.info("✅ Saved offer %s (%s)", card.id_solicitud, card.empresa)

            # Human-pacing throttle
            time.sleep(random.uniform(settings.inter_modal_min_s, settings.inter_modal_max_s))

        if not goto_next_page(driver, settings):
            break
        page += 1
        wait_results_or_empty(driver, settings)

    log.info(
        "Done. New: %d | Skipped: %d | Failed: %d | Total known: %d",
        new_count, skipped, failed, len(existing_ids),
    )


if __name__ == "__main__":
    main()

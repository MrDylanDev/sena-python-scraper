"""Browser session lifecycle.

Builds an `undetected_chromedriver.Chrome` instance configured for SENA
scraping and tears it down cleanly. Visible by default (headless mode is
opt-in via Settings; SENA's overlay heuristics are more reliable with a
visible window).
"""

from __future__ import annotations

import logging

import undetected_chromedriver as uc

from .config import Settings

log = logging.getLogger(__name__)


def build_driver(settings: Settings) -> uc.Chrome:
    """Create a Chrome driver tuned for the SENA portal."""
    options = uc.ChromeOptions()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(settings.page_load_timeout)
    try:
        driver.maximize_window()
    except Exception:
        # Some headless modes don't support maximize_window; not fatal.
        pass
    log.info("Chrome driver started (headless=%s)", settings.headless)
    return driver


def close_driver(driver: uc.Chrome) -> None:
    """Quit the driver, swallowing any teardown errors."""
    try:
        driver.quit()
        log.info("Chrome driver closed")
    except Exception as exc:  # noqa: BLE001 — teardown best-effort
        log.warning("Error while closing driver: %s", exc)

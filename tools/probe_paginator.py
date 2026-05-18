"""Probe paginator: log in, navigate, filter Antioquia, dump paginator + bottom.

Goal: understand the actual DOM structure of the SENA pagination control
so navigation.goto_next_page can match it correctly.

Captures:
- Full results page HTML
- Screenshot of the bottom of the page
- HTML of any element matching common paginator id/class candidates
- Every <a> and <button> with text containing "siguiente", "next", "ver más", arrows
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from selenium.webdriver.common.by import By  # noqa: E402

from sena_scraper.config import load_settings  # noqa: E402
from sena_scraper.login import login_aprendiz  # noqa: E402
from sena_scraper.navigation import filter_departamento, goto_solicitudes, wait_results_or_empty  # noqa: E402
from sena_scraper.session import build_driver, close_driver  # noqa: E402

DEBUG_DIR = Path("data/debug")
log = logging.getLogger("probe_paginator")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    driver = build_driver(settings)
    try:
        login_aprendiz(driver, settings)
        goto_solicitudes(driver, settings)
        filter_departamento(driver, settings)
        wait_results_or_empty(driver, settings)
        time.sleep(2)  # let AJAX settle

        # Scroll to bottom so the paginator is in view (if it lazy-renders)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Save full page HTML + screenshot
        html_path = DEBUG_DIR / "results_page.html"
        html_path.write_text(driver.page_source, encoding="utf-8")
        log.info("📄 Full HTML: %s (%d bytes)", html_path, len(driver.page_source))

        png_path = DEBUG_DIR / "results_bottom.png"
        driver.save_screenshot(str(png_path))
        log.info("📸 Bottom screenshot: %s", png_path)

        # Try the configured paginator id
        log.info("=" * 60)
        log.info("PAGINATOR by id='div_solicitudes_paginas'")
        log.info("=" * 60)
        paginators = driver.find_elements(By.ID, "div_solicitudes_paginas")
        log.info("Count: %d", len(paginators))
        for p in paginators:
            html = (p.get_attribute("outerHTML") or "")[:2000]
            log.info("OuterHTML (first 2000 chars):\n%s", html)

        # Try other common paginator candidates
        log.info("=" * 60)
        log.info("ALTERNATIVE PAGINATOR CANDIDATES")
        log.info("=" * 60)
        candidates = [
            "div[id*='pagina']",
            "div[class*='pagin']",
            "ul.pagination",
            "nav[aria-label*='pag']",
            "[id*='siguiente']",
            "[class*='siguiente']",
        ]
        for css in candidates:
            els = driver.find_elements(By.CSS_SELECTOR, css)
            if els:
                log.info("  %s → %d match(es)", css, len(els))
                for el in els[:3]:
                    snippet = (el.get_attribute("outerHTML") or "")[:500]
                    log.info("    %s", snippet.replace("\n", " "))

        # Buttons and anchors with promising text
        log.info("=" * 60)
        log.info("ANCHORS / BUTTONS WITH PAGINATION-LIKE TEXT")
        log.info("=" * 60)
        keywords = ("siguiente", "next", "ver más", "ver mas", "más", "›", ">>", "→")
        for tag in ("a", "button"):
            for el in driver.find_elements(By.TAG_NAME, tag):
                text = (el.text or "").strip().lower()
                aria = (el.get_attribute("aria-label") or "").lower()
                title = (el.get_attribute("title") or "").lower()
                onclick = (el.get_attribute("onclick") or "")
                blob = f"{text} {aria} {title}"
                if any(kw in blob for kw in keywords):
                    log.info(
                        "  <%s> text=%r aria=%r title=%r onclick=%s href=%s",
                        tag,
                        text[:40],
                        aria[:40],
                        title[:40],
                        onclick[:80],
                        (el.get_attribute("href") or "")[:80],
                    )

        # All numeric anchors (page numbers)
        log.info("=" * 60)
        log.info("NUMERIC ANCHORS (page numbers)")
        log.info("=" * 60)
        for a in driver.find_elements(By.TAG_NAME, "a"):
            text = (a.text or "").strip()
            if text.isdigit():
                log.info(
                    "  <a> text=%s href=%s onclick=%s class=%s",
                    text,
                    (a.get_attribute("href") or "")[:80],
                    (a.get_attribute("onclick") or "")[:80],
                    (a.get_attribute("class") or "")[:50],
                )

    finally:
        close_driver(driver)

    return 0


if __name__ == "__main__":
    sys.exit(main())

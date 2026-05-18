"""Navigation through the Solicitudes search/filter/pagination flow.

Public functions:
    goto_solicitudes(driver, settings) -> None
    filter_departamento(driver, settings) -> None
    wait_results_or_empty(driver, settings) -> bool   # True if results present
    iter_card_buttons(driver) -> list[WebElement]     # all "Ver - Aplicar" buttons on this page
    goto_next_page(driver) -> bool                    # True if jumped, False if no more
"""

from __future__ import annotations

import logging

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Settings
from .constants import (
    CARD_BTN_VER_APLICAR_CSS,
    PAGINATOR_BTN_SIGUIENTE,
    RESULT_DIV_PAGINAS,
    RESULT_DIV_SOLICITUDES,
    RESULT_DIV_VACIO,
    RESULT_LBL_TOTAL,
    SEARCH_BTN_BUSCAR,
    SEARCH_SEL_DEPARTAMENTO,
)
from .errors import LoginFailed, NavigationFailed
from .overlays import remove_loading_overlays

log = logging.getLogger(__name__)


def goto_solicitudes(driver: WebDriver, settings: Settings) -> None:
    """Navigate to the Solicitudes search page via the dashboard menu.

    IMPORTANT: ``driver.get(settings.solicitudes_url)`` directly returns
    HTTP 500 (NullReferenceException) because the server-side controller
    relies on session state set when the user navigates from the menu.
    We therefore:

    1. Load ``/Aprendices/Index`` (the dashboard) — this works directly.
    2. Find the menu anchor whose href ends in ``/Aprendices/Solicitudes``
       (with or without trailing slash).
    3. Click it via JS (the link may be inside a collapsed mobile nav).
    4. Wait for ``#sel_departamento`` to appear (the search filter).

    Raises:
        LoginFailed: if the dashboard load bounces back to login.aspx.
        NavigationFailed: on any other timeout/missing element.
    """
    # If we are already on the dashboard (e.g., right after login), do
    # NOT re-fetch — the SENA portal occasionally invalidates a fresh
    # session if hit twice in quick succession on the same URL.
    if "/Aprendices/Index" in driver.current_url:
        log.info("Already on dashboard at %s — skipping reload",
                 driver.current_url)
    else:
        log.info("Loading dashboard %s", settings.dashboard_url)
        driver.get(settings.dashboard_url)

    # Login-bounce check: if the portal punted us back to login.aspx,
    # the session never established (or expired).
    current = driver.current_url.lower()
    if "login.aspx" in current:
        raise LoginFailed(
            f"Dashboard load redirected to login (URL: {driver.current_url}). "
            "Session not established."
        )

    # Find the Solicitudes menu anchor. The href may include a trailing
    # slash; we normalize before matching.
    try:
        WebDriverWait(driver, settings.page_load_timeout).until(
            lambda d: any(
                (a.get_attribute("href") or "").rstrip("/").endswith(
                    "/Aprendices/Solicitudes"
                )
                for a in d.find_elements(By.TAG_NAME, "a")
            )
        )
    except TimeoutException as exc:
        raise NavigationFailed(
            "Dashboard loaded but Solicitudes menu link did not appear "
            f"within {settings.page_load_timeout}s"
        ) from exc

    target = None
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = (a.get_attribute("href") or "").rstrip("/")
        if href.endswith("/Aprendices/Solicitudes"):
            target = a
            break
    if target is None:  # defensive — wait above should have ensured this
        raise NavigationFailed("Solicitudes menu anchor disappeared after wait")

    log.info("Clicking menu link: %s", target.get_attribute("href"))
    # JS click handles links nested in collapsed nav menus.
    driver.execute_script("arguments[0].click();", target)

    # Wait for the search form's department selector to render.
    try:
        WebDriverWait(driver, settings.page_load_timeout).until(
            EC.presence_of_element_located((By.ID, SEARCH_SEL_DEPARTAMENTO))
        )
    except TimeoutException as exc:
        raise NavigationFailed(
            f"Solicitudes page did not render within "
            f"{settings.page_load_timeout}s (current URL: {driver.current_url})"
        ) from exc

    remove_loading_overlays(driver)


def filter_departamento(driver: WebDriver, settings: Settings) -> None:
    """Set the department filter and click Buscar.

    The SENA portal populates the ``<select>`` options asynchronously
    after the page loads, and may use a CSS-based custom dropdown that
    hides the native ``<option>`` elements. ``Select.select_by_value``
    fails in either case (ElementNotInteractable). We:

    1. Wait for the select to be present.
    2. Wait until the select actually has multiple options (proves the
       SENA JS finished populating it).
    3. Set the value via JS + dispatch a 'change' event — robust against
       hidden options and custom dropdown wrappers.
    4. Click Buscar.
    """
    log.info("Filtering by department value=%s", settings.departamento_value)
    wait = WebDriverWait(driver, settings.page_load_timeout)

    sel_el = wait.until(
        EC.presence_of_element_located((By.ID, SEARCH_SEL_DEPARTAMENTO))
    )

    # Wait for the select to be populated (more than the placeholder option).
    wait.until(
        lambda d: len(
            d.find_elements(
                By.CSS_SELECTOR, f"#{SEARCH_SEL_DEPARTAMENTO} option"
            )
        )
        > 1
    )

    # Set value via JS — bypasses ElementNotInteractable when options are
    # hidden by a custom dropdown plugin.
    driver.execute_script(
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
        sel_el,
        settings.departamento_value,
    )

    btn = wait.until(EC.element_to_be_clickable((By.ID, SEARCH_BTN_BUSCAR)))
    btn.click()


def wait_results_or_empty(driver: WebDriver, settings: Settings) -> bool:
    """Wait until the result list renders OR the empty-state shows.

    Returns True when at least one card is present. False when the empty
    state is visible. Raises NavigationFailed on timeout.
    """
    wait = WebDriverWait(driver, settings.page_load_timeout)

    def has_results_or_empty(d: WebDriver) -> bool:
        try:
            cards = d.find_elements(
                By.CSS_SELECTOR, f"#{RESULT_DIV_SOLICITUDES} {CARD_BTN_VER_APLICAR_CSS}"
            )
            if cards:
                return True
            empty = d.find_element(By.ID, RESULT_DIV_VACIO)
            return empty.is_displayed()
        except NoSuchElementException:
            return False

    try:
        wait.until(has_results_or_empty)
    except TimeoutException as exc:
        raise NavigationFailed(
            "Search results did not render within "
            f"{settings.page_load_timeout}s"
        ) from exc

    remove_loading_overlays(driver)

    cards = driver.find_elements(
        By.CSS_SELECTOR, f"#{RESULT_DIV_SOLICITUDES} {CARD_BTN_VER_APLICAR_CSS}"
    )
    has_cards = len(cards) > 0
    log.info("Page rendered: %d card(s) found", len(cards))
    return has_cards


def iter_card_buttons(driver: WebDriver) -> list[WebElement]:
    """Return all visible Ver-Aplicar buttons on the current page.

    Buttons are returned fresh on every call (the SENA DOM re-renders
    after pagination, so callers must NOT cache references across pages).
    """
    return driver.find_elements(
        By.CSS_SELECTOR,
        f"#{RESULT_DIV_SOLICITUDES} {CARD_BTN_VER_APLICAR_CSS}",
    )


def goto_next_page(driver: WebDriver, settings: Settings) -> bool:
    """Click the "Siguiente" button to advance to the next page.

    Returns True if the page advanced, False if there is no next page.

    SENA's paginator (verified May 2026) uses two ``<button>`` elements
    inside ``#div_solicitudes_paginas`` — NOT anchor links:

        button#btn_pagina_anterior   — display:none on page 1
        button#btn_pagina_siguiente  — display:none on the last page
        label#lbl_total_solicitudes  — e.g. "0 a 20 de 25"

    The button is hidden when there are no more pages, so we treat
    "not displayed" as the end-of-pagination signal.
    """
    import time as _time

    # The paginator only fully hydrates after the viewport reaches the
    # bottom AND the lazy-load has shipped all cards in the current page.
    # Loop the scroll until the card count stops growing.
    prev_count = -1
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        _time.sleep(1.5)
        count = driver.execute_script(
            "return document.querySelectorAll("
            "'#div_solicitudes .divSolicitudRequeridaCasilla'"
            ").length;"
        )
        if count == prev_count:
            break
        prev_count = count

    try:
        btn = driver.find_element(By.ID, PAGINATOR_BTN_SIGUIENTE)
    except NoSuchElementException:
        log.info("Paginator button missing; pagination ended")
        return False

    if not btn.is_displayed() or not btn.is_enabled():
        log.info("Siguiente button hidden/disabled; pagination ended")
        return False

    # Log the current range/total if available (helps observability).
    try:
        lbl = driver.find_element(By.ID, RESULT_LBL_TOTAL)
        progress = (lbl.text or "").strip()
        if progress:
            log.info("Pagination progress: %s", progress)
    except NoSuchElementException:
        pass

    try:
        driver.execute_script("arguments[0].click();", btn)
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to click Siguiente: %s", exc)
        return False

    # The Siguiente button stays in the DOM after click; the cards inside
    # #div_solicitudes refresh via AJAX. Sleep a few seconds to let the
    # XHR complete, then strip overlays.
    _time.sleep(3)
    remove_loading_overlays(driver)

    # Defensive: confirm the results container is still present.
    WebDriverWait(driver, settings.page_load_timeout).until(
        EC.presence_of_element_located((By.ID, RESULT_DIV_SOLICITUDES))
    )
    log.info("Advanced to next page")
    return True

"""SENA learner portal login.

Credentials are passed via Selenium `send_keys` ONLY. We never interpolate
them into a JavaScript template string (that would be unsafe when a value
contains quotes or backslashes).

Login is intermittent on the SENA portal: the form's tab-switcher
(Empresas/Aprendices) sometimes loses to the deferred submit click,
leaving the session unauthenticated. To make this deterministic we:

1. Submit the credentials.
2. Poll `current_url` for up to 25s waiting for the URL to leave
   `login.aspx` (success indicator — the portal redirects to
   `/Aprendices/Index` once authenticated).
3. If still on login.aspx, retry the full submit flow up to 3 times.
"""

from __future__ import annotations

import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Settings
from .constants import (
    LOGIN_BTN_SUBMIT,
    LOGIN_INPUT_PASSWORD,
    LOGIN_INPUT_USUARIO,
    LOGIN_TAB_APRENDICES,
)
from .errors import LoginFailed
from .overlays import remove_loading_overlays

log = logging.getLogger(__name__)

# Empirically derived: the portal needs a few seconds after submit for
# the session cookies to settle. We poll afterwards instead of sleeping
# blindly — see _wait_for_login_redirect.
POST_SUBMIT_SETTLE_SECONDS = 3
LOGIN_REDIRECT_TIMEOUT_SECONDS = 25
LOGIN_MAX_ATTEMPTS = 3
LOGIN_URL_FRAGMENT = "login.aspx"


def login_aprendiz(driver: WebDriver, settings: Settings) -> None:
    """Submit the learner credentials with verification and retry.

    Raises:
        LoginFailed: if after ``LOGIN_MAX_ATTEMPTS`` submit attempts the
            URL never leaves ``login.aspx`` within
            ``LOGIN_REDIRECT_TIMEOUT_SECONDS`` per attempt.
    """
    for attempt in range(1, LOGIN_MAX_ATTEMPTS + 1):
        log.info("Login attempt %d/%d", attempt, LOGIN_MAX_ATTEMPTS)
        _submit_login(driver, settings)

        if _wait_for_login_redirect(driver, LOGIN_REDIRECT_TIMEOUT_SECONDS):
            log.info(
                "✅ Login confirmed — URL is %s",
                driver.current_url,
            )
            remove_loading_overlays(driver)
            return

        log.warning(
            "Login attempt %d did not redirect away from login.aspx "
            "within %ds (URL=%s)",
            attempt,
            LOGIN_REDIRECT_TIMEOUT_SECONDS,
            driver.current_url,
        )

    raise LoginFailed(
        f"Login did not establish a session after {LOGIN_MAX_ATTEMPTS} "
        f"attempts. URL still: {driver.current_url}"
    )


def _submit_login(driver: WebDriver, settings: Settings) -> None:
    """Single submit pass: open page, fill credentials, click submit."""
    log.info("Opening login page %s", settings.login_url)
    driver.get(settings.login_url)
    wait = WebDriverWait(driver, settings.page_load_timeout)

    # 1. Click the "Aprendices" tab. Native click first (fires the full
    # mouse event sequence the SENA tab handler may listen for); fall
    # back to JS click if the native click is intercepted by an overlay.
    tab = wait.until(EC.presence_of_element_located((By.ID, LOGIN_TAB_APRENDICES)))
    try:
        tab.click()
    except Exception as exc:  # noqa: BLE001 — click may be overlay-intercepted
        log.warning("Native tab click failed (%s); using JS click fallback", exc)
        driver.execute_script("arguments[0].click();", tab)
    time.sleep(1)

    # 2. Defensive DOM fix: force the aprendiz submit visible and the
    # empresa submit hidden, regardless of whether the tab handler ran.
    # The form has TWO submit inputs (`ini_session_empresa` visible by
    # default, `ini_session_aprendiz` display:none). The portal decides
    # the auth mode by which button is submitted; if `ini_session_empresa`
    # gets clicked, the session is established as anonymous-empresa and
    # the next protected page renders with usuarioActual=null (HTTP 500).
    driver.execute_script(
        """
        var emp = document.getElementById('ini_session_empresa');
        var apr = document.getElementById(arguments[0]);
        if (emp) emp.style.display = 'none';
        if (apr) apr.style.display = '';
        """,
        LOGIN_BTN_SUBMIT,
    )

    # 3. Fill credentials via send_keys (NEVER interpolate into JS).
    user_input = wait.until(
        EC.visibility_of_element_located((By.ID, LOGIN_INPUT_USUARIO))
    )
    user_input.clear()
    user_input.send_keys(settings.usuario)

    pass_input = driver.find_element(By.ID, LOGIN_INPUT_PASSWORD)
    pass_input.clear()
    pass_input.send_keys(settings.password)

    # 4. Submit the aprendiz button via a setTimeout-deferred JS click.
    # A direct `arguments[0].click()` makes execute_script wait for the
    # renderer's response, but the click triggers a navigation that
    # blocks that response — Selenium times out at 60s. Deferring the
    # click via setTimeout lets execute_script return immediately while
    # the click+POST happen asynchronously in the browser.
    driver.execute_script(
        """
        var id = arguments[0];
        setTimeout(function(){
            var btn = document.getElementById(id);
            if (btn) btn.click();
        }, 100);
        """,
        LOGIN_BTN_SUBMIT,
    )
    log.info("Login submitted as APRENDIZ; polling for redirect")
    time.sleep(POST_SUBMIT_SETTLE_SECONDS)


def _wait_for_login_redirect(driver: WebDriver, timeout: int) -> bool:
    """Poll for the URL to leave ``login.aspx``.

    Returns True if the URL leaves login.aspx within ``timeout`` seconds.
    Returns False otherwise.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        url = driver.current_url
        if LOGIN_URL_FRAGMENT not in url.lower():
            return True
        time.sleep(1)
    return False

"""Remove SENA's loading overlays via JavaScript injection.

The SENA portal leaves modal-backdrop, updProgress and similar AJAX overlays
behind after a navigation, blocking subsequent clicks. This module sweeps
them out without affecting application state.
"""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from .constants import OVERLAY_CLASSES, OVERLAY_IDS

# Keep the JS small and idempotent. It only removes known leftovers and
# restores body scroll/opacity if the portal disabled them.
_REMOVE_JS = """
const ids = arguments[0];
const classes = arguments[1];
ids.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
classes.forEach(cls => {
  document.querySelectorAll('.' + cls).forEach(el => el.remove());
});
document.body.style.overflow = 'auto';
document.body.style.opacity = '1';
return true;
"""


def remove_loading_overlays(driver: WebDriver) -> None:
    """Best-effort removal of SENA AJAX overlays. Never raises."""
    try:
        driver.execute_script(_REMOVE_JS, OVERLAY_IDS, OVERLAY_CLASSES)
    except Exception:
        # Overlay sweep is opportunistic; never break the run if JS fails.
        pass

"""Per-offer extraction.

The SENA modal does NOT expose the company name — that lives on the card
in the result list. So we read company + id_solicitud from the card BEFORE
opening the modal, then open the modal and read everything else.

Public types:
    OfferCard   — what we read from a result-list card (pre-click)
    ModalData   — what we read from the open modal (post-click)
    Offer       — the canonical merged record persisted to JSONL
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

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
    CARD_BTN_DATA_ID,
    CARD_EMPRESA_CSS,
    MODAL_BTN_CERRAR,
    MODAL_LBL_CIUDAD,
    MODAL_LBL_CONTACTO,
    MODAL_LBL_DEPARTAMENTO,
    MODAL_LBL_EMAIL,
    MODAL_LBL_ESPECIALIDAD,
    MODAL_LBL_FECHA_CIERRE,
    MODAL_LBL_TELEFONO,
)
from .errors import ExtractionFailed

log = logging.getLogger(__name__)


# ---------------- Dataclasses ----------------


@dataclass(frozen=True)
class OfferCard:
    """Data read from a result-list card (before opening the modal)."""

    id_solicitud: str
    empresa: str


@dataclass(frozen=True)
class ModalData:
    """Data read from an open offer modal."""

    correo: str
    telefono: str
    programa: str
    departamento: str
    ciudad: str
    contacto: str
    fecha_cierre: str


@dataclass(frozen=True)
class Offer:
    """Canonical merged record persisted to JSONL."""

    id_solicitud: str
    empresa: str
    correo: str
    telefono: str
    programa: str
    departamento: str
    ciudad: str
    contacto: str
    fecha_cierre: str
    fecha_extraccion: str  # ISO 8601 UTC

    @classmethod
    def merge(cls, card: OfferCard, modal: ModalData) -> Offer:
        return cls(
            id_solicitud=card.id_solicitud,
            empresa=card.empresa,
            correo=modal.correo,
            telefono=modal.telefono,
            programa=modal.programa,
            departamento=modal.departamento,
            ciudad=modal.ciudad,
            contacto=modal.contacto,
            fecha_cierre=modal.fecha_cierre,
            fecha_extraccion=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


# ---------------- Card-level read ----------------


def read_card(button_el: WebElement) -> OfferCard:
    """Extract id_solicitud + empresa from a card given its Ver-Aplicar button.

    The card layout (verified May 2026) is:
        div.divSolicitudRequeridaCasilla
          └─ ...
            ├─ label.aprendizLabelTituloSolicitudesBA  ← empresa
            ├─ ...
            └─ button.aprendizBotonInternoNaranja[data-id-solicitud=N]
    """
    # data-id-solicitud sits on the button itself.
    id_sol = (button_el.get_attribute(CARD_BTN_DATA_ID) or "").strip()
    if not id_sol:
        raise ExtractionFailed(
            "Card button missing data-id-solicitud attribute", id_solicitud=None
        )

    # Walk up to the nearest .divSolicitudRequeridaCasilla, then find the
    # company-name label inside it.
    try:
        casilla = button_el.find_element(
            By.XPATH, "ancestor::div[contains(@class,'divSolicitudRequeridaCasilla')][1]"
        )
        empresa_el = casilla.find_element(By.CSS_SELECTOR, CARD_EMPRESA_CSS)
        empresa = (empresa_el.text or "").strip()
    except NoSuchElementException as exc:
        raise ExtractionFailed(
            f"Could not locate empresa label for id_solicitud={id_sol}",
            id_solicitud=id_sol,
        ) from exc

    if not empresa:
        raise ExtractionFailed(
            f"Empty empresa label for id_solicitud={id_sol}", id_solicitud=id_sol
        )

    return OfferCard(id_solicitud=id_sol, empresa=empresa)


def read_all_cards(driver: WebDriver) -> list[OfferCard]:
    """Snapshot all visible card data via a single JS call.

    This is the stale-safe alternative to ``read_card``. It returns plain
    string data — no ``WebElement`` references are held across calls — so
    subsequent DOM updates (AJAX filter, pagination, modal close) cannot
    invalidate the result.

    Lazy-load behavior: the SENA results panel only renders the full
    batch (up to 20 cards) AND the paginator's "Siguiente" button after
    the viewport reaches the bottom. We therefore scroll to the bottom
    and let the server respond before snapshotting.

    Cards missing ``data-id-solicitud`` or empty empresa label are
    silently skipped.
    """
    import time as _time

    # Trigger lazy-load: scroll to bottom repeatedly until the card
    # count stops growing. The SENA panel ships cards in progressive
    # batches; a single scroll is not enough to load the full first page.
    prev_count = -1
    for _ in range(10):  # safety bound
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

    raw = driver.execute_script(
        """
        var out = [];
        var cards = document.querySelectorAll(
            '#div_solicitudes .divSolicitudRequeridaCasilla'
        );
        for (var i = 0; i < cards.length; i++) {
            var btn = cards[i].querySelector('button.aprendizBotonInternoNaranja');
            var lbl = cards[i].querySelector('label.aprendizLabelTituloSolicitudesBA');
            out.push({
                id: btn ? (btn.getAttribute('data-id-solicitud') || '') : '',
                empresa: lbl ? (lbl.textContent || '').trim() : ''
            });
        }
        return out;
        """
    )
    cards: list[OfferCard] = []
    for r in raw or []:
        id_sol = (r.get("id") or "").strip()
        empresa = (r.get("empresa") or "").strip()
        if id_sol and empresa:
            cards.append(OfferCard(id_solicitud=id_sol, empresa=empresa))
    return cards


def find_card_button(driver: WebDriver, id_solicitud: str) -> WebElement | None:
    """Re-resolve a card's Ver-Aplicar button fresh by ``id_solicitud``.

    Returns the button element, or None if no card with that id exists
    on the current page (e.g. it was filtered out or pagination moved).
    """
    try:
        return driver.find_element(
            By.CSS_SELECTOR,
            f"button.aprendizBotonInternoNaranja[data-id-solicitud='{id_solicitud}']",
        )
    except NoSuchElementException:
        return None


# ---------------- Modal-level read ----------------


def open_modal(
    driver: WebDriver, button_el: WebElement, settings: Settings, id_solicitud: str
) -> None:
    """Click a Ver-Aplicar button and wait until the modal is visible
    (the email label having non-empty text is our readiness signal)."""
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button_el
        )
        driver.execute_script("arguments[0].click();", button_el)
    except Exception as exc:
        raise ExtractionFailed(
            f"Failed to click Ver-Aplicar for id_solicitud={id_solicitud}: {exc}",
            id_solicitud=id_solicitud,
        ) from exc

    wait = WebDriverWait(driver, settings.modal_timeout)

    def email_has_text(d: WebDriver) -> bool:
        try:
            el = d.find_element(By.ID, MODAL_LBL_EMAIL)
            return bool((el.text or "").strip())
        except NoSuchElementException:
            return False

    try:
        wait.until(email_has_text)
    except TimeoutException as exc:
        raise ExtractionFailed(
            f"Modal did not load (email empty) for id_solicitud={id_solicitud}",
            id_solicitud=id_solicitud,
        ) from exc


def _label_text(driver: WebDriver, label_id: str) -> str:
    try:
        return (driver.find_element(By.ID, label_id).text or "").strip()
    except NoSuchElementException:
        return ""


def read_modal(driver: WebDriver, id_solicitud: str) -> ModalData:
    """Read the modal labels into a ModalData. Email and telefono are
    required; missing them raises ExtractionFailed."""
    correo = _label_text(driver, MODAL_LBL_EMAIL)
    telefono = _label_text(driver, MODAL_LBL_TELEFONO)
    programa = _label_text(driver, MODAL_LBL_ESPECIALIDAD)
    departamento = _label_text(driver, MODAL_LBL_DEPARTAMENTO)
    ciudad = _label_text(driver, MODAL_LBL_CIUDAD)
    contacto = _label_text(driver, MODAL_LBL_CONTACTO)
    fecha_cierre = _label_text(driver, MODAL_LBL_FECHA_CIERRE)

    if not correo:
        raise ExtractionFailed(
            f"Modal email empty for id_solicitud={id_solicitud}",
            id_solicitud=id_solicitud,
        )

    return ModalData(
        correo=correo,
        telefono=telefono,
        programa=programa,
        departamento=departamento,
        ciudad=ciudad,
        contacto=contacto,
        fecha_cierre=fecha_cierre,
    )


def close_modal(driver: WebDriver) -> None:
    """Close the modal via its Cerrar button. Falls back to ESC on failure.
    Never raises — the caller must continue regardless."""
    try:
        btn = driver.find_element(By.ID, MODAL_BTN_CERRAR)
        driver.execute_script("arguments[0].click();", btn)
        return
    except (NoSuchElementException, Exception):  # noqa: BLE001
        pass
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")  # ESC
    except Exception:  # noqa: BLE001
        log.warning("Could not close modal cleanly; continuing anyway")

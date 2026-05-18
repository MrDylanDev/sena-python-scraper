"""SENA portal DOM selectors and URL constants.

Centralized so a portal-side DOM change requires editing exactly one file.
Verified against the live portal during the SDD design phase (May 2026).

Selector groups:
- LOGIN_*  — login page elements
- SEARCH_* — search/filter form on /Solicitudes/
- CARD_*   — per-offer card in the result list
- MODAL_*  — per-offer modal (opened via "Ver - Aplicar")
"""

from __future__ import annotations

# ----- Login page -----
LOGIN_TAB_APRENDICES = "aprendices"  # button#aprendices
LOGIN_INPUT_USUARIO = "tbLoginUsuario"  # input#tbLoginUsuario
LOGIN_INPUT_PASSWORD = "__tbPasswordUsuario"  # input#__tbPasswordUsuario
LOGIN_BTN_SUBMIT = "ini_session_aprendiz"  # button#ini_session_aprendiz

# ----- Search / filter form -----
SEARCH_SEL_DEPARTAMENTO = "sel_departamento"  # select#sel_departamento
SEARCH_BTN_BUSCAR = "btn_buscar_solicitud"  # button#btn_buscar_solicitud (text "Buscar")

# ----- Results container -----
RESULT_DIV_SOLICITUDES = "div_solicitudes"  # div#div_solicitudes
RESULT_DIV_VACIO = "div_solicitudes_vacio"  # div#div_solicitudes_vacio
RESULT_LBL_TOTAL = "lbl_total_solicitudes"  # label#lbl_total_solicitudes
RESULT_DIV_PAGINAS = "div_solicitudes_paginas"  # div#div_solicitudes_paginas
PAGINATOR_BTN_SIGUIENTE = "btn_pagina_siguiente"  # button#btn_pagina_siguiente
PAGINATOR_BTN_ANTERIOR = "btn_pagina_anterior"  # button#btn_pagina_anterior

# ----- Per-offer card -----
# Each card is `div.divSolicitudRequeridaCasilla` inside `#div_solicitudes`.
CARD_CSS = "#div_solicitudes .divSolicitudRequeridaCasilla"
# First label inside a card carries the company name.
CARD_EMPRESA_CSS = "label.aprendizLabelTituloSolicitudesBA"
# The Ver-Aplicar button inside a card (id is duplicated across cards — DON'T use it).
# Use class + text match. The orange button class is the most reliable selector.
CARD_BTN_VER_APLICAR_CSS = "button.aprendizBotonInternoNaranja"
# Data attribute on the button carries the unique solicitud id.
CARD_BTN_DATA_ID = "data-id-solicitud"

# ----- Modal (opened by clicking Ver-Aplicar) -----
MODAL_LBL_ESPECIALIDAD = "lbl_modal_solicitud_especialidad"
MODAL_LBL_DEPARTAMENTO = "lbl_modal_solicitud_dpto"
MODAL_LBL_CIUDAD = "lbl_modal_solicitud_ciudad"
MODAL_LBL_CONTACTO = "lbl_modal_solicitud_contacto"
MODAL_LBL_DIRECCION = "lbl_modal_solicitud_direccion"
MODAL_LBL_TELEFONO = "lbl_modal_solicitud_telefono"
MODAL_LBL_EMAIL = "lbl_modal_solicitud_email"
MODAL_LBL_PERFIL = "lbl_modal_solicitud_perfil"
MODAL_LBL_FUNCIONES = "lbl_modal_solicitud_funciones"
MODAL_LBL_REQUERIDOS = "lbl_modal_solicitud_requeridos"
MODAL_LBL_APLICADOS = "lbl_modal_solicitud_aplicados"
MODAL_LBL_FECHA_CREACION = "lbl_modal_solicitud_fecha_creacion"
MODAL_LBL_FECHA_CIERRE = "lbl_modal_solicitud_fecha_cierre"

MODAL_BTN_APLICAR = "btn_modal_solicitud_aplicar"  # CRITICAL: NEVER click this
MODAL_BTN_CERRAR = "btn_modal_solicitud_cerrar"

# ----- Loading overlays -----
# IDs/classes the SENA portal leaves behind after AJAX calls.
OVERLAY_IDS = ["updProgress", "updProgress1", "IMGDIV", "preloader", "loader"]
OVERLAY_CLASSES = ["overLayBackground", "modal-backdrop", "modalCargando"]

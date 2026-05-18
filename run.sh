#!/usr/bin/env bash
# run.sh — pipeline completa del bot SENA: scraper + emailer
#
# Uso:
#   ./run.sh              # interactivo: scrapea, hace preview, pregunta antes de mandar
#   ./run.sh --dry-run    # solo scrapea + preview (NUNCA manda)
#   ./run.sh --send       # scrapea + manda directo (sin preview, modo explícito)
#
# Siempre se ejecuta desde el directorio del proyecto, sin importar
# desde dónde lo invoques.

set -euo pipefail

# Resolver el directorio real del script y posicionarse ahí
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="./venv/bin/python"

# Validar que el venv exista
if [[ ! -x "$PYTHON" ]]; then
    echo "❌ venv no encontrado en $PYTHON"
    echo ""
    echo "Para crearlo desde cero:"
    echo "   python3 -m venv venv"
    echo "   ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Validar que .env exista
if [[ ! -f .env ]]; then
    echo "❌ Falta el archivo .env. Copialo desde .env.example y llená:"
    echo "   - SENA_USUARIO, SENA_PASSWORD, SENA_TIPO_DOCUMENTO"
    echo "   - GMAIL_USER, GMAIL_APP_PASSWORD"
    exit 1
fi

MODE="${1:-interactive}"

echo "════════════════════════════════════════════════"
echo "  SENA ADSO Bot — pipeline completa"
echo "════════════════════════════════════════════════"
echo ""

# ──────────── Paso 1: Scrapeo ────────────
echo "▶ Paso 1: Scrapeando ofertas ADSO Antioquia del SENA..."
echo "  (el navegador se va a abrir; cierra solo al final)"
echo ""
"$PYTHON" main.py
echo ""

# ──────────── Paso 2 + 3: Emails ────────────
case "$MODE" in
    --dry-run)
        echo "▶ Paso 2: Preview de emails (sin enviar)"
        echo ""
        "$PYTHON" send_applications.py --dry-run
        echo ""
        echo "✅ Listo. NINGÚN email enviado (modo --dry-run)."
        ;;

    --send)
        echo "▶ Paso 2: Enviando emails directo (modo --send, sin preview)"
        echo ""
        "$PYTHON" send_applications.py
        echo ""
        echo "✅ Pipeline completa."
        ;;

    interactive|*)
        echo "▶ Paso 2: Preview de emails (no envía nada todavía)"
        echo ""
        "$PYTHON" send_applications.py --dry-run
        echo ""
        echo "════════════════════════════════════════════════"
        read -r -p "¿Mandar los emails reales? [s/N]: " confirm
        echo ""
        if [[ "$confirm" =~ ^[Ss]$ ]]; then
            echo "▶ Paso 3: Enviando emails (con pacing 30-60s)..."
            echo ""
            "$PYTHON" send_applications.py
            echo ""
            echo "✅ Pipeline completa."
        else
            echo "❌ Cancelado. Ningún email enviado."
            exit 0
        fi
        ;;
esac

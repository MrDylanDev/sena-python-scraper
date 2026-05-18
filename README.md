# SENA ADSO Antioquia Offer Extractor

Automated scraper that logs into the SENA learner portal (`caprendizaje.sena.edu.co`), searches sponsorship offers filtered by department (Antioquia), extracts contact details from each offer modal, filters for the ADSO program (Análisis y Desarrollo de Software), and persists results to a local JSONL file with idempotency guarantees.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment template and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your SENA portal credentials
   ```

## Run

```bash
python main.py
```

Output is written to `data/ofertas_adso_antioquia.jsonl`. Re-running the script skips offers already extracted (idempotent by `id_solicitud`).

## Sending applications

Sends a personalized application email to each contact in `data/ofertas_adso_antioquia.jsonl` via Gmail SMTP, with dual-source idempotency (local log + IMAP Sent folder).

### Setup

1. Add Gmail credentials to `.env`:
   ```
   GMAIL_USER=your.email@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```

2. Generate an App Password at: https://myaccount.google.com/apppasswords
   (requires 2FA enabled on the Google account).

### Usage

```bash
# Preview all emails without sending
python send_applications.py --dry-run

# Send for real (30-60s pacing between emails)
python send_applications.py
```

Output is appended to `data/envios.jsonl`. Re-running skips contacts already sent to (idempotent).

### Output schema (`data/envios.jsonl`)

| Field | Type | Description |
|-------|------|-------------|
| `id_solicitud` | string | Source offer identifier |
| `empresa` | string | Company name |
| `correo` | string | Recipient (lowercased) |
| `subject` | string | Rendered subject |
| `status` | string | `sent`, `failed`, or `invalid_email` |
| `error` | string | Empty when sent; error detail otherwise |
| `timestamp` | string | ISO 8601 UTC |

### Troubleshooting

- **Authentication error**: Regenerate the App Password at the URL above. Ensure 2FA is active.
- **IMAP folder not found**: Check your Gmail account language. The bot auto-detects `[Gmail]/Sent Mail` (English) and `[Gmail]/Enviados` (Spanish).
- **Rate limit warnings**: Emails are already paced 30-60s apart. If Gmail still flags, wait 24h before retrying.

## Output Schema

Each line in the JSONL file is a JSON object with 10 fields:

| Field | Type | Description |
|-------|------|-------------|
| `id_solicitud` | string | Unique SENA offer identifier |
| `empresa` | string | Company name (from result card) |
| `correo` | string | Contact email |
| `telefono` | string | Contact phone |
| `programa` | string | Academic program (always contains "ANALISIS Y DESARROLLO DE SOFTWARE") |
| `departamento` | string | Department (Antioquia) |
| `ciudad` | string | City |
| `contacto` | string | Contact person name |
| `fecha_cierre` | string | Offer closing date |
| `fecha_extraccion` | string | ISO 8601 UTC timestamp of extraction |

## Legal Disclaimer

This tool is intended for **personal use only** by SENA learners who are already authorized to access the data through the portal.

**Habeas Data — Ley 1581 de 2012 (Colombia)**: Contact information extracted by this tool (emails, phone numbers, names) constitutes personal data protected under Colombian data protection law. The operator is solely responsible for ensuring that any use of this data complies with the principles of purpose limitation, necessity, and prior authorization established by Ley 1581 de 2012 and its regulatory decrees.

**SENA Terms of Service**: Use of this tool must comply with the terms of service of `caprendizaje.sena.edu.co`. Automated access may be restricted or prohibited by SENA's acceptable use policies. The operator assumes all responsibility for compliance.

**The authors of this tool provide no warranty and accept no liability for misuse of extracted data or violations of applicable regulations.**

## Troubleshooting

### ChromeDriver version mismatch

`undetected-chromedriver` auto-downloads a compatible ChromeDriver binary. If Chrome updates and the cached driver is stale:

```bash
rm -rf ~/.local/share/undetected_chromedriver/
python main.py  # will re-download
```

### Login timeout

If login fails with a timeout error:
- Verify credentials in `.env` are correct
- Check that the SENA portal is accessible (sometimes under maintenance)
- Try increasing `page_load_timeout` in `src/sena_scraper/config.py`

### Modal close failures

If the bot logs "Could not close modal cleanly":
- This is non-fatal — the bot sends ESC as fallback and continues
- If it happens repeatedly, the SENA portal may have changed its modal structure
- Check `src/sena_scraper/constants.py` for `MODAL_BTN_CERRAR` selector accuracy

### Python 3.12+ distutils error

`undetected-chromedriver` depends on `distutils` (removed in Python 3.12). Install `setuptools`:

```bash
pip install setuptools
```

# StockFlow MVP — Project Status

## What's Complete

### Foundation
- **CLAUDE.md** — full MVP spec including parsing rules, data integrity rules, approval/safety rules, and anti-scope-creep rules

### Parser
- **parser.py** — parses raw WhatsApp text; extracts `item`, `quantity`, `unit`; numeric confidence scoring (0.0–1.0); unit normalization (`litres` → `l`, `boxes` → `box`, etc.); `raw_input` stored verbatim; defaults quantity to 1 + confidence 0.5 when missing

### API
- **api.py** — FastAPI wrapper exposing `POST /parse`; tested locally at `http://127.0.0.1:8000/parse`
- **requirements.txt** — `fastapi`, `uvicorn`, `gspread`, `google-auth`; all dependencies installed

### Data Layer
- **sheets_writer.py** — writes parsed result to Google Sheets; auto-creates worksheet per business with correct headers; `confidence` excluded from sheet (internal only); placeholder `credentials.json` and `SPREADSHEET_ID` — not yet live

### Testing
- **test_pipeline.py** — end-to-end pipeline test: `parse_message` → `write_parsed_result` with mocked Google Sheets; confirmed correct field mapping, `status: pending`, timestamp in ISO 8601
- **Local API test** — `POST /parse` with `"3 litres milk"` returned correct JSON (`unit: l`, `confidence: 0.9`)

### Make.com Design
- Full per-message capture flow documented: webhook → router → `/parse` → Google Sheets → WhatsApp reply
- Exact module config specified: HTTP method, field mapping, Twilio response body, confidence filter (≥ 0.5)

## Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project rules and MVP spec |
| `parser.py` | Core parsing logic |
| `api.py` | FastAPI `/parse` endpoint |
| `sheets_writer.py` | Google Sheets writer |
| `test_pipeline.py` | End-to-end pipeline test (no credentials needed) |
| `requirements.txt` | Python dependencies |
| `PROJECT_STATUS.md` | This file |
| `StockFlow_ Revised Strategic Brief.md` | Reference: stack analysis, upscaling roadmap |
| `StockFlow_ Comprehensive Analysis of Challenges and Solutions.md` | Reference: challenge/solution framework |

## Next Step

**Expose the API and wire Make.com:**

1. Run `ngrok http 8000` to get a public URL for the local FastAPI server
2. In Make.com Module 2, set URL to the ngrok URL: `https://xxxx.ngrok.io/parse`
3. Configure Twilio/360dialog webhook to point to the Make.com custom webhook URL
4. Build the Make.com scenario with the four designed modules
5. Send a live WhatsApp test message and confirm the row lands in Google Sheets

Once the live test passes, the core data path — receive → parse → store — is validated.

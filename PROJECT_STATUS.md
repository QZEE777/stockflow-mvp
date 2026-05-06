# StockFlow MVP — Project Status

## What's Complete

### Foundation
- **CLAUDE.md** — full MVP spec including parsing rules, data integrity rules, approval/safety rules, and anti-scope-creep rules

### Parser
- **parser.py** — parses raw WhatsApp text; extracts `item`, `quantity`, `unit`; numeric confidence scoring (0.0–1.0); unit normalisation (`litres` → `l`, `boxes` → `box`, etc.); `raw_input` stored verbatim; defaults quantity to 1 + confidence 0.5 when missing; handles multi-item messages

### API
- **api.py** — FastAPI wrapper exposing `POST /parse`; tested locally at `http://127.0.0.1:8000/parse`
- **requirements.txt** — `fastapi`, `uvicorn`, `gspread`, `google-auth`; all dependencies installed

### Data Layer
- **sheets_writer.py** — writes parsed result to Google Sheets; loops over all items from parser output and writes one row per item; auto-creates worksheet per business with correct headers; `confidence` excluded from sheet (internal only); credentials and spreadsheet ID read from environment variables (`GOOGLE_CREDENTIALS_FILE`, `SPREADSHEET_ID`) — not hardcoded

### Testing
- **test_pipeline.py** — end-to-end pipeline test: `parse_message` → `write_parsed_result` with mocked Google Sheets; verified correct field mapping, `status: pending`, timestamp in ISO 8601; passes cleanly

### Security
- **credentials.json** and **.env** added to `.gitignore` — Google service account credentials will never be committed
- Credentials and spreadsheet ID are environment variables, not source constants

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

## Not Yet Built (in order of priority)

| Step | What's needed |
|---|---|
| **Live Sheets write** | Set `GOOGLE_CREDENTIALS_FILE` and `SPREADSHEET_ID` env vars; test `write_parsed_result` against a real sheet |
| **Make.com scenario** | Build 4-module flow: Twilio webhook → HTTP `/parse` → Sheets append → Twilio reply |
| **Low-confidence clarification** | Route confidence < 0.5 to WhatsApp button message instead of Sheets write |
| **Consolidation** | Merge identical `item` + `unit` rows within same business + calendar day into summary range |
| **Owner confirmation flow** | Send full consolidated list to owner; accept CONFIRM/EDIT; gate on registered owner number only |
| **24-hour reminder** | One reminder if no CONFIRM received; list stays pending — never auto-confirms |
| **Order output** | Send confirmed list as supplier order/shopping list |

## Next Step

**Wire the live data path:**

1. Create a Google service account; download `credentials.json` (not committed — in `.gitignore`)
2. Set environment variables:
   ```
   GOOGLE_CREDENTIALS_FILE=credentials.json
   SPREADSHEET_ID=<your sheet id>
   ```
3. Run `uvicorn api:app --reload`
4. Run `ngrok http 8000` to expose a public URL
5. In Make.com Module 2, set URL to `https://xxxx.ngrok.io/parse`
6. Configure Twilio/360dialog webhook to point to Make.com custom webhook URL
7. Build the Make.com 4-module scenario
8. Send a live WhatsApp test message — confirm the row lands in Google Sheets

Once the live test passes, the core data path — receive → parse → store — is validated.

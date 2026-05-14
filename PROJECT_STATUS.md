# StockFlow MVP — Project Status

**Last updated:** 2026-05-14

---

## What's Built and Working

### Infrastructure
- **API** (`api.py`) — FastAPI, running on port 8001
- **Tunnel** — ngrok at `https://backhand-return-groggily.ngrok-free.dev` (persistent, still live)
- **Google Sheets** — Spreadsheet ID `1v-bZ8lLudqbJMiSltvz1GTmNRW-cueM9e2SZmXh0994`
- **Service account** — `stockflow-writer@stockflow-495512.iam.gserviceaccount.com`

### Pipeline (confirmed end-to-end)
```
WhatsApp message → Twilio → Make.com webhook → HTTP /parse → Google Sheets row written
```

### Parser (`parser.py`)
- Extracts item, quantity, unit from free-text WhatsApp messages
- Intent detection: `order_request`, `low_stock`, `stock_count`
- `stock_count` items NOT written to sheet — acknowledged only
- `low_stock` written to sheet with qty=1, confidence=0.4
- Filler word stripping (leading + trailing)
- Variant expansion: "sugar sachets white and brown" → two items
- 10/10 tests passing

### Normalizer (`normalizer.py`)
- Alias map (black labels → black label, jamesons → jamison, etc.)
- Conservative singularization
- 12/12 tests passing

### Schema v2 (`sheets_writer.py`)
10 columns:
```
business_id | user_phone | timestamp | raw_input | item | normalized_item | quantity | unit | status | intent
```
Old rows fall back gracefully (normalized_item → item, intent → order_request)

### Consolidation (`consolidate.py` + `/consolidate` endpoint)
- Reads pending rows for a business + date
- Groups by normalized_item, sums quantities
- Low_stock items marked "qty unclear" if no order quantity exists
- Writes structured output to `daily_summary` tab
- Returns WhatsApp-ready text summary
- CLI: `python consolidate.py <business_id> [YYYY-MM-DD]`
- API: `POST /consolidate` with `{business_id, date}`

### Make.com Scenario
3 modules:
1. **Webhooks** — custom webhook receives Twilio payload
2. **HTTP POST /parse** — calls API, gets parsed result + whatsapp_confirmation
3. **HTTP POST → Twilio REST API** — sends reply back to staff ← **NOT YET TESTED**

Module 3 config:
- URL: `https://api.twilio.com/2010-04-01/Accounts/ACe503815a44c710394294ccb5979c5e/Messages.json`
- Auth: Basic (twilio-stockflow keychain)
- Body (form-encoded):
  - `From` = `whatsapp:+14155238886`
  - `To` = `1. From` (staff's WhatsApp number from webhook)
  - `Body` = `3. data: whatsapp_confirmation` (from HTTP /parse response)

---

## Files

| File | Purpose |
|---|---|
| `api.py` | FastAPI — /parse and /consolidate endpoints |
| `parser.py` | Core parsing logic with intent detection |
| `normalizer.py` | Deterministic item name normalisation |
| `consolidate.py` | Consolidation engine + daily_summary writer |
| `sheets_writer.py` | Google Sheets writer (schema v2) |
| `test_pipeline.py` | End-to-end pipeline test (4/4 passing) |
| `requirements.txt` | Python dependencies |
| `credentials.json` | Google service account key (gitignored) |
| `.env` | GOOGLE_CREDENTIALS_FILE + SPREADSHEET_ID (gitignored) |

---

## Next Steps (in order)

### 1. Test reply-back ← NEXT ACTION
- Open Make.com scenario
- Click Run once
- Send WhatsApp message to `+1 415 523 8886`
- Confirm reply arrives on phone with "Logged: - X item"
- If Twilio REST call fails, check execution log for error detail

### 2. Owner confirmation flow
- Trigger: owner sends CONFIRM / EDIT / thumbs up to the Twilio number
- Gate: only registered owner phone can trigger
- On CONFIRM: update all today's pending rows to confirmed
- On EDIT: pause and prompt for change
- Send one reminder after 24h if no response

### 3. Daily owner digest
- Wire /consolidate endpoint to a Make.com scheduled scenario
- Trigger: daily at a set time (e.g., 5pm)
- Send consolidated list to owner's WhatsApp
- Owner replies CONFIRM or EDIT

### 4. Persistent hosting
- ngrok URL changes on reboot — not suitable for production
- Move API to a cheap VPS (DigitalOcean/Hetzner, ~R50-100/month)
- Set env vars on server, run uvicorn as a service

### 5. PARKED (post-MVP)
- Voice message transcription
- Staff name to phone mapping
- Low-confidence clarification buttons
- Supplier-ready order export
- Multi-location support
- Analytics / reporting

---

## Startup Checklist (every session)
```
1. cd "C:\Users\qqfs7\Desktop\stockflow mvp"
2. python -m uvicorn api:app --port 8001  (run in background)
3. Check ngrok: curl https://backhand-return-groggily.ngrok-free.dev/parse
4. If tunnel dead: ngrok http 8001
5. Public URL: https://backhand-return-groggily.ngrok-free.dev
```

---

## Credentials Reference
- **Twilio number:** +1 415 523 8886
- **Twilio join code:** join same-spend
- **Twilio Account SID:** ACe503815a44c710394294ccb5979c5e
- **Twilio Auth Token:** get fresh from console.twilio.com each session
- **Make.com webhook URL:** https://hook.eu1.make.com/bbpqgf3mholj98vikomq1gna1h2c6lz7
- **Make.com scenario:** Integration Webhooks, HTTP — ON (Immediately as data arrives)
- **Google Sheet:** https://docs.google.com/spreadsheets/d/1v-bZ8lLudqbJMiSltvz1GTmNRW-cueM9e2SZmXh0994

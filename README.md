# StockFlow MVP

**Your stock, on WhatsApp.**

StockFlow is a conversation-first stock ordering and operational memory system for small businesses.

---

## The Problem

Small hospitality and retail businesses run on informal communication — WhatsApp messages, voice notes, verbal requests, paper notes, and human memory. That chaos causes stockouts, costs money, and creates operational risk.

---

## The Solution

StockFlow sits in the middle and converts that chaos into structured operational data.

A staff member sends:
```
"Need 5 milk, 2 boxes eggs and maybe more water tomorrow."
```

StockFlow returns:
```json
{
  "items": [
    { "item": "milk", "quantity": 5, "unit": "units", "confidence": 0.9 },
    { "item": "eggs", "quantity": 2, "unit": "box", "confidence": 0.85 },
    { "item": "water", "quantity": 1, "unit": "units", "confidence": 0.5 }
  ],
  "raw_input": "Need 5 milk, 2 boxes eggs and maybe more water tomorrow.",
  "status": "pending"
}
```

---

## Who It's For

Small hospitality and retail businesses:
- Restaurants, cafes, bars
- Guest houses and hotels
- Food trucks and kitchens
- Small grocery operations

Especially businesses where WhatsApp already functions as the unofficial operating system.

---

## What's Been Built

| Phase | What it delivered |
|---|---|
| Phase 1 | Proved messy real-world language can become structured data |
| Phase 2 | Core parser — handles structured, semi-structured, and messy input |
| Phase 3 | Operational memory layer — raw + parsed storage, confidence scoring, traceability |
| Phase 4 | FastAPI service layer, webhook foundations, Google Sheets output, pipeline testing |

---

## Current Stack

| Component | Technology |
|---|---|
| API Layer | FastAPI (Python) |
| NLP Engine | Rule-based parser (Python) |
| Data Format | JSON |
| Integration | Webhooks, Make.com |
| Output | Google Sheets |

---

## Repo Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Full MVP spec and rules for AI coding agents |
| `parser.py` | Core parsing logic |
| `api.py` | FastAPI `/parse` endpoint |
| `sheets_writer.py` | Google Sheets writer |
| `test_pipeline.py` | End-to-end pipeline test |
| `requirements.txt` | Python dependencies |
| `PROJECT_STATUS.md` | Current build status and next steps |

---

## Current MVP Status

This is a functional technical MVP — not a finished SaaS product.

Working:
- Parser tested and accurate locally
- API running locally at `POST /parse`
- Google Sheets writer built (credentials pending)
- Full pipeline tested end-to-end with mocks

Next step: connect to the real world via ngrok + Make.com + live WhatsApp test.

---

## What This Is Not

Not a POS system. Not inventory software. Not a customer-facing bot.

The competitors are pen and paper, notes apps, informal WhatsApp chats, and spreadsheets.

---

*Built by Zed — Plettenberg Bay, South Africa.*

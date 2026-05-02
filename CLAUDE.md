# StockFlow — MVP

**Tagline:** "Your stock, on WhatsApp."

StockFlow is a WhatsApp-based stock capture and ordering system for SMBs. Staff send text or voice messages about stock needs; the system parses, consolidates, and turns them into a confirmed supplier order or shopping list.

---

## What StockFlow IS

A shared operational memory layer that converts real-time human input (via WhatsApp) into structured, actionable stock tasks.

## What StockFlow is NOT

Not a POS system. Not inventory software. Not a customer-facing ordering bot. The competitors are pen & paper, notes apps, informal WhatsApp chats, and spreadsheets — not Shopify or Lightspeed.

Reinforce this in every piece of copy: "Send your stock on WhatsApp. We handle the rest."

---

## MVP Scope

Only these capabilities ship in v1:

| Step | What happens |
|---|---|
| **Input** | Staff send WhatsApp text or voice: "Need 5kg sirloin", "Low on Black Label" |
| **Parsing** | AI extracts: `item`, `quantity`, `unit`, `user`, `business`, `timestamp` |
| **Consolidation** | Duplicates merged into one unified daily list per business |
| **Confirmation** | Owner receives summary → replies CONFIRM or EDIT |
| **Output** | Confirmed list sent as supplier order or shopping list |

**Out of scope for MVP — park it:** analytics dashboards, POS integration, accounting integration, multi-location, supplier price checks, in-WhatsApp payments, freemium tier, advanced reporting, customer-facing bots.

---

## Tech Stack

Chosen for speed of validation, not scale. Do not pre-build for scale.

| Layer | MVP choice | Why |
|---|---|---|
| **Messaging** | WhatsApp Business API via Twilio or 360dialog | Fast to set up; 360dialog cheaper at volume |
| **Automation / backend** | Make.com | Visual workflows, no-code, rapid prototyping |
| **Data storage** | Google Sheets (one sheet per business) | Accessible, zero setup, fine for MVP volume |
| **AI parsing** | Claude API or OpenAI API | Strong NL extraction from messy free text |

**Known post-MVP upgrades — do not implement yet:**
- Make.com → n8n (self-hosted) or custom Python/Node backend
- Google Sheets → Supabase / PostgreSQL
- Add confidence scoring + human-in-the-loop on low-confidence parses

**Google Sheets concurrency note:** Sheets is not designed for simultaneous writes. For MVP volumes this is acceptable; it becomes a problem at scale — that is the Supabase migration trigger.

---

## Data Schema (per captured stock item)

```
business_id      - which business this belongs to
user_phone       - staff member who sent the message
timestamp        - when it was captured (ISO 8601)
raw_input        - original message verbatim (keep for AI retraining)
item             - parsed item name
quantity         - parsed numeric quantity
unit             - parsed unit (kg, units, bottles, etc.)
status           - pending | confirmed | edited | cancelled
```

Store `raw_input` from day one. It is the training data for future fine-tuning and the audit trail for disputes.

---

## WhatsApp Interaction Rules

- **Clarification before re-parsing:** If AI extraction is ambiguous, send an interactive button/list message ("Did you mean 5kg sirloin? [Yes] [No, edit]") rather than silently guessing or asking for a free-text retry.
- **Stay in the 24-hour window:** Prefer responses within the user-initiated service conversation window (free-form, no template charge). Use approved template messages only when re-engaging outside that window.
- **Owner confirmation is non-negotiable:** No order leaves the system without an explicit CONFIRM reply from the owner. Never auto-send.

---

## Parsing Rules (MVP)

- Extract exactly: `item`, `quantity`, `unit`. Nothing else from the message content.
- If quantity is missing, default to 1 and mark as low-confidence for optional clarification.
- If item is unclear, send a clarification button message. Do not silently discard or guess.
- Voice messages: transcribe first, then parse the transcript with the same rules.
- Treat variations of the same item ("sirloin", "sirloin steak", "steak") as distinct until the owner maps them — do not auto-merge item names.
- Always store `raw_input` exactly as received, before any parsing or transformation.
- Return structured JSON from the parser: `{ item, quantity, unit, confidence, raw_input }`. Confidence is for internal routing only — not shown to users in MVP.

---

## Data Integrity Rules

- `raw_input` is immutable once written. Never overwrite it.
- Status transitions are one-directional: `pending → confirmed`, `pending → edited`, `pending → cancelled`. No reversals.
- Deduplication merges quantities for identical `item` + `unit` within the same `business_id` and calendar day. Do not merge across days.
- Never hard-delete a row. Use `status: cancelled` instead.
- The Google Sheet for each business is append-only for raw captures. Consolidation writes to a separate summary range, not back into raw rows.

---

## Approval / Safety Rules

- An order is only sent when the owner sends a confirmation intent. Accept: `yes`, `ok`, `confirm`, `send`, `👍` (case-insensitive). Never infer confirmation from unrelated messages.
- `EDIT` pauses the list and prompts the owner for the change. No partial sends.
- If no confirmation is received within 24 hours, the list stays in `pending`. Do not auto-confirm. Do not auto-expire silently — send one reminder only.
- The confirmation message sent to the owner must include the full consolidated list. Never send a truncated summary for confirmation.
- Only the registered owner number for a business can confirm or trigger an edit. Staff messages cannot trigger an order.

---

## Anti-Scope-Creep Rules

- If a feature is not in the MVP Scope table, it does not get built — not even a stub, placeholder, or "we'll fill this in later" field.
- Do not add columns to the Google Sheet schema that serve future features. Schema additions require a deliberate decision, not convenience.
- Do not build any UI, web interface, or dashboard. WhatsApp is the only interface in MVP.
- Do not integrate with any system other than: WhatsApp Business API, Make.com, Google Sheets, and the AI parsing API.
- When a new idea arises during build, add it to a `PARKED.md` file. Do not discuss it further until MVP is validated.

---

## Target Market — Phase 1 Only

Mobile coffee stalls, market traders, small cafés, salons.

Restaurants, liquor outlets, supermarkets, and spaza shops are later phases — do not design around their needs yet.

---

## Business Model

7–14 day free trial → R99–R199/month per business. No one-time purchase. Tiered pricing and add-ons are post-MVP.

---

## Go-to-Market — Stage 1 Only

Founder-led direct onboarding via personal networks. Referrals, testimonials, and a landing page come in Stage 2.

---

## Operating Principles

1. **Strict MVP discipline.** If a feature is not in the scope table above, it does not ship in v1.
2. **No app switching, no training.** Anything that pulls a user out of WhatsApp is a regression.
3. **Owner confirmation is non-negotiable** before any order is sent.
4. **Capture `raw_input` from day one** — future fine-tuning, supplier mapping, and analytics need it.
5. **Keep workflows and schema migration-clean.** Make.com flows and Sheets columns should lift into n8n/Supabase later without a rewrite. Avoid hard-coding anything that belongs in a database.

---

## Key Risks

| Risk | Mitigation |
|---|---|
| Messy NL input lowers parse accuracy | Use WhatsApp interactive buttons/lists for clarification *before* reaching for fine-tuning |
| WhatsApp API per-message cost erodes margin | Maximise the 24-hour service-conversation window; avoid unnecessary template messages |
| Positioning drift (users expect a POS) | Every copy touchpoint reinforces the operational-memory framing |
| POPIA / data privacy (South Africa) | Clear privacy policy, encrypted transit + storage, collect minimum PII |
| Scope creep | Anything not in the MVP scope table is parked, not added |

---

## Reference Documents

- `StockFlow_ Revised Strategic Brief.md` — tech stack analysis, upscaling roadmap, provider comparisons.
- `StockFlow_ Comprehensive Analysis of Challenges and Solutions.md` — challenge/solution deep-dives across technical, market, legal, and strategic domains.

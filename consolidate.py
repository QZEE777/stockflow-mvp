"""
consolidate.py

Reads pending order rows from a business's Google Sheet tab,
groups by normalized_item, sums quantities, and produces a clean
daily shopping list. Writes output to the daily_summary tab.

No AI. Deterministic grouping only.
"""
import os
import sys
from datetime import date, datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SUMMARY_TAB = "daily_summary"
SUMMARY_HEADERS = ["date", "item", "quantity", "unit", "note"]


def _get_spreadsheet():
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    spreadsheet_id = os.getenv("SPREADSHEET_ID", "")
    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(spreadsheet_id)


def _get_or_create_tab(spreadsheet, tab_name: str, headers: list):
    try:
        sheet = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
        sheet.append_row(headers)
    return sheet


def consolidate(business_id: str, target_date: date = None) -> str:
    """
    Consolidate pending orders for a business on a given date.

    Returns a plain-text summary suitable for WhatsApp delivery to the owner.
    Also writes structured output to the daily_summary tab.
    """
    if target_date is None:
        target_date = date.today()

    date_str = str(target_date)  # YYYY-MM-DD
    spreadsheet = _get_spreadsheet()

    # --- Read raw rows ---
    try:
        raw_sheet = spreadsheet.worksheet(business_id)
    except gspread.WorksheetNotFound:
        return f"No data found for business: {business_id}"

    rows = raw_sheet.get_all_records()

    # --- Filter: pending + today + order or low_stock ---
    pending = [
        r for r in rows
        if r.get("status") == "pending"
        and str(r.get("timestamp", ""))[:10] == date_str
        and r.get("intent", "order_request") in ("order_request", "low_stock")
    ]

    if not pending:
        return f"No pending orders for {business_id} on {date_str}."

    # --- Group and sum by normalized_item ---
    totals = {}

    for row in pending:
        # Prefer normalized_item; fall back to item for older rows without it
        key = (str(row.get("normalized_item") or row.get("item", "")).strip().lower())
        if not key:
            continue

        unit = str(row.get("unit", "unit") or "unit").strip()
        intent = str(row.get("intent", "order_request")).strip()

        try:
            qty = int(float(row.get("quantity", 1)))
        except (ValueError, TypeError):
            qty = 1

        if key not in totals:
            totals[key] = {
                "quantity": 0,
                "unit": unit,
                "has_order": False,
                "has_low_stock": False,
            }

        if intent == "low_stock":
            totals[key]["has_low_stock"] = True
            # Do not add the default qty=1 to the sum — quantity is unclear
        else:
            totals[key]["quantity"] += qty
            totals[key]["has_order"] = True

    # --- Build structured rows ---
    summary_rows = []
    for name in sorted(totals.keys()):
        data = totals[name]
        qty = data["quantity"]
        unit = data["unit"]
        has_order = data["has_order"]
        has_low_stock = data["has_low_stock"]
        display = name.title()

        if has_order and has_low_stock:
            note = "low stock also flagged"
        elif has_low_stock and not has_order:
            note = "low stock — qty unclear"
            qty = ""
            unit = ""
        else:
            note = ""

        summary_rows.append({
            "item": display,
            "quantity": qty,
            "unit": unit,
            "note": note,
        })

    # --- Write to daily_summary tab ---
    _write_summary(spreadsheet, date_str, summary_rows)

    # --- Build WhatsApp-ready text ---
    date_label = target_date.strftime("%d %B %Y")
    lines = [f"STOCKFLOW — {date_label}", ""]

    for row in summary_rows:
        name = row["item"]
        qty = row["quantity"]
        unit = row["unit"]
        note = row["note"]

        if not qty and not unit:
            line = f"- {name} (low stock — qty unclear)"
        elif unit == "unit":
            line = f"- {name} x {qty}"
        else:
            line = f"- {name} x {qty} {unit}"

        if note and "low stock" not in note:
            line += f" ({note})"

        lines.append(line)

    return "\n".join(lines)


def _write_summary(spreadsheet, date_str: str, summary_rows: list):
    """
    Write consolidated rows to the daily_summary tab.
    Clears previous entries for the same date, appends new ones.
    """
    sheet = _get_or_create_tab(spreadsheet, SUMMARY_TAB, SUMMARY_HEADERS)
    all_values = sheet.get_all_values()

    # Find rows belonging to today and remove them
    rows_to_keep = [row for row in all_values if row and row[0] != date_str]
    sheet.clear()
    for row in rows_to_keep:
        sheet.append_row(row)

    # If sheet is now empty (was cleared), write headers
    remaining = sheet.get_all_values()
    if not remaining:
        sheet.append_row(SUMMARY_HEADERS)

    # Append today's consolidated rows
    for row in summary_rows:
        sheet.append_row([
            date_str,
            row["item"],
            row["quantity"],
            row["unit"],
            row["note"],
        ])


if __name__ == "__main__":
    business_id = sys.argv[1] if len(sys.argv) > 1 else "whatsapp:+14155238886"
    target = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    print(consolidate(business_id, target))

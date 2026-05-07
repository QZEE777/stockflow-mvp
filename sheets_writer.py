import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = [
    "business_id", "user_phone", "timestamp", "raw_input",
    "item", "normalized_item", "quantity", "unit", "status", "intent"
]


def _get_sheet(business_id: str):
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    spreadsheet_id = os.getenv("SPREADSHEET_ID", "")
    creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        return spreadsheet.worksheet(business_id)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=business_id, rows=1000, cols=len(HEADERS))
        sheet.append_row(HEADERS)
        return sheet


def write_parsed_result(parsed: dict, business_id: str, user_phone: str) -> None:
    sheet = _get_sheet(business_id)
    timestamp = datetime.now(timezone.utc).isoformat()
    for item in parsed["items"]:
        sheet.append_row([
            business_id,
            user_phone,
            timestamp,
            parsed["raw_input"],
            item["name"],
            item.get("normalized_item", item["name"]),  # fallback for old rows
            item["quantity"],
            item["unit"],
            "pending",
            item.get("intent", "order_request"),        # fallback for old rows
        ])

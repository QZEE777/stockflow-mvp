import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone

CREDENTIALS_FILE = "credentials.json"  # placeholder — not included in repo
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"  # placeholder — set before use
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = ["business_id", "user_phone", "timestamp", "raw_input",
           "item", "quantity", "unit", "status"]


def _get_sheet(business_id: str):
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        return spreadsheet.worksheet(business_id)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=business_id, rows=1000, cols=8)
        sheet.append_row(HEADERS)
        return sheet


def write_parsed_result(parsed: dict, business_id: str, user_phone: str) -> None:
    sheet = _get_sheet(business_id)
    sheet.append_row([
        business_id,
        user_phone,
        datetime.now(timezone.utc).isoformat(),
        parsed["raw_input"],
        parsed["item"],
        parsed["quantity"],
        parsed["unit"],
        "pending",
    ])

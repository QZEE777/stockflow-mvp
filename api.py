from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")  # explicit path

from fastapi import FastAPI
from pydantic import BaseModel
from parser import parse_message
from sheets_writer import write_parsed_result

app = FastAPI()


class ParseRequest(BaseModel):
    message: str
    business_id: str
    user_phone: str


def build_whatsapp_confirmation(parsed: dict) -> str:
    """
    Build a WhatsApp reply based on intent:
    - order_request / low_stock: "Logged: - X item"
    - stock_count: "Got it - X item on hand noted."
    """
    order_items = [i for i in parsed.get("items", []) if i.get("intent") != "stock_count"]
    stock_items = [i for i in parsed.get("items", []) if i.get("intent") == "stock_count"]

    lines = []

    if order_items:
        lines.append("Logged:")
        for item in order_items:
            qty = item.get("quantity", 1)
            unit = item.get("unit", "unit")
            name = item.get("name", "unknown item")
            if unit == "unit":
                lines.append(f"- {qty} {name}")
            else:
                lines.append(f"- {qty} {unit} {name}")

    for item in stock_items:
        qty = item.get("quantity", 1)
        name = item.get("name", "unknown item")
        lines.append(f"Got it - {qty} {name} on hand noted.")

    return "\n".join(lines)


@app.post("/parse")
def parse(request: ParseRequest):
    parsed = parse_message(request.message)

    # Only write order_request and low_stock items to the sheet.
    # stock_count items are acknowledged only — they do not enter the order pipeline.
    items_to_write = [i for i in parsed["items"] if i.get("intent") != "stock_count"]
    if items_to_write:
        write_parsed_result(
            {"items": items_to_write, "raw_input": parsed["raw_input"]},
            request.business_id,
            request.user_phone
        )

    return {
        **parsed,
        "whatsapp_confirmation": build_whatsapp_confirmation(parsed)
    }

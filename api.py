from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")  # must run before sheet imports

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date as date_type
from typing import Optional

from parser import parse_message
from normalizer import normalize_item
from sheets_writer import write_parsed_result
from consolidate import consolidate as run_consolidate

app = FastAPI()


class ParseRequest(BaseModel):
    message: str
    business_id: str
    user_phone: str


class ConsolidateRequest(BaseModel):
    business_id: str
    date: Optional[str] = None  # YYYY-MM-DD; defaults to today


def build_whatsapp_confirmation(parsed: dict) -> str:
    """
    Build a WhatsApp reply based on intent:
    - order_request / low_stock  → "Logged: - X item"
    - stock_count                → "Got it - X item on hand noted."
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

    # Add normalized_item to each item before writing
    for item in parsed["items"]:
        item["normalized_item"] = normalize_item(item["name"])

    # Only write order_request and low_stock to the sheet.
    # stock_count is acknowledged only — does not enter the order pipeline.
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


@app.post("/consolidate")
def consolidate_endpoint(request: ConsolidateRequest):
    target = date_type.fromisoformat(request.date) if request.date else date_type.today()
    summary = run_consolidate(request.business_id, target)
    return {
        "summary": summary,
        "business_id": request.business_id,
        "date": str(target),
    }

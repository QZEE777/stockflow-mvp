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
    lines = ["Logged:"]

    for item in parsed.get("items", []):
        quantity = item.get("quantity", 1)
        unit = item.get("unit", "unit")
        name = item.get("name", "unknown item")

        if unit == "unit":
            lines.append(f"- {quantity} {name}")
        else:
            lines.append(f"- {quantity} {unit} {name}")

    return "\n".join(lines)


@app.post("/parse")
def parse(request: ParseRequest):
    parsed = parse_message(request.message)
    write_parsed_result(parsed, request.business_id, request.user_phone)

    return {
        **parsed,
        "whatsapp_confirmation": build_whatsapp_confirmation(parsed)
    }

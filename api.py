from fastapi import FastAPI
from pydantic import BaseModel
from parser import parse_message

app = FastAPI()


class ParseRequest(BaseModel):
    message: str


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

    return {
        **parsed,
        "whatsapp_confirmation": build_whatsapp_confirmation(parsed)
    }
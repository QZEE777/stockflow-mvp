import re
import json

UNITS = [
    'boxes', 'box', 'bottles', 'bottle', 'packs', 'pack', 'bags', 'bag',
    'units', 'unit', 'pieces', 'piece', 'crates', 'crate', 'tins', 'tin',
    'cans', 'can', 'sachets', 'sachet', 'dozens', 'dozen',
    'kg', 'grams', 'gram', 'g', 'litres', 'litre', 'liters', 'liter', 'ml', 'l',
]

_UNIT_NORM = {
    'litres': 'l', 'litre': 'l', 'liters': 'l', 'liter': 'l',
    'grams': 'g', 'gram': 'g',
    'boxes': 'box',
    'bottles': 'bottle',
}

_FILLER = re.compile(
    r'^(need|low on|running low on|out of|we need|please get|get|order|i need)\s+',
    re.IGNORECASE
)

_WITH_UNIT = re.compile(
    rf'^(\d+(?:\.\d+)?)\s*({"|".join(UNITS)})\s+(.+)$',
    re.IGNORECASE
)

_NUMBER_ONLY = re.compile(r'^(\d+(?:\.\d+)?)\s+(.+)$')


def parse_message(raw_input: str) -> dict:
    text = _FILLER.sub('', raw_input.strip())

    m = _WITH_UNIT.match(text)
    if m:
        qty = float(m.group(1))
        raw_unit = m.group(2).lower()
        result = {
            "item": m.group(3).strip().lower(),
            "quantity": int(qty) if qty == int(qty) else qty,
            "unit": _UNIT_NORM.get(raw_unit, raw_unit),
            "confidence": 0.9,
            "raw_input": raw_input,
        }

    elif _NUMBER_ONLY.match(text):
        m = _NUMBER_ONLY.match(text)
        qty = float(m.group(1))
        result = {
            "item": m.group(2).strip().lower(),
            "quantity": int(qty) if qty == int(qty) else qty,
            "unit": "units",
            "confidence": 0.8,
            "raw_input": raw_input,
        }

    else:
        result = {
            "item": text.strip().lower(),
            "quantity": 1,
            "unit": "units",
            "confidence": 0.5,
            "raw_input": raw_input,
        }

    if len(result["item"]) <= 1:
        result["confidence"] = 0.3

    return result


if __name__ == "__main__":
    tests = [
        "Need 5kg chicken",
        "low on milk",
        "2 boxes eggs",
    ]
    for msg in tests:
        print(json.dumps(parse_message(msg), indent=2))

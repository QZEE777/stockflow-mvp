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
    'packs': 'pack',
    'bags': 'bag',
    'pieces': 'piece',
    'crates': 'crate',
    'tins': 'tin',
    'cans': 'can',
    'sachets': 'sachet',
    'dozens': 'dozen',
    'units': 'unit',
}

_FILLER = re.compile(
    r'^(need|low on|running low on|out of|we need|please get|get|order|i need|only)\s+',
    re.IGNORECASE
)

_TRAILING_FILLER = re.compile(
    r'\s+\b(left|remaining|please|asap|urgently|urgent)\b.*$',
    re.IGNORECASE
)

_ITEM_PATTERN = re.compile(
    rf'(\d+(?:\.\d+)?)\s*({"|".join(UNITS)})?\s+([a-zA-Z][a-zA-Z\s]*?)(?=\s+\d+|$)',
    re.IGNORECASE
)


def _clean_item(item: str) -> str:
    item = item.strip().lower()
    item = re.sub(r'\b(and|plus|also)\b', '', item).strip()
    return item


def _clean_quantity(qty: float):
    return int(qty) if qty == int(qty) else qty


def parse_message(raw_input: str) -> dict:
    text = raw_input.strip().lower()
    text = _FILLER.sub('', text)
    text = _TRAILING_FILLER.sub('', text)
    text = text.replace(',', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    items = []

    for match in _ITEM_PATTERN.finditer(text):
        qty = float(match.group(1))
        raw_unit = match.group(2).lower() if match.group(2) else 'unit'
        item = _clean_item(match.group(3))

        if not item:
            continue

        items.append({
            "name": item,
            "quantity": _clean_quantity(qty),
            "unit": _UNIT_NORM.get(raw_unit, raw_unit),
            "confidence": 0.9 if match.group(2) else 0.8,
        })

    if not items and " and " in text:
        parts = [p.strip() for p in text.split(" and ") if p.strip()]
        for p in parts:
            items.append({
                "name": p,
                "quantity": 1,
                "unit": "unit",
                "confidence": 0.6,
            })

    if not items:
        items.append({
            "name": text,
            "quantity": 1,
            "unit": "unit",
            "confidence": 0.5,
        })

    return {
        "items": items,
        "raw_input": raw_input,
    }


if __name__ == "__main__":
    tests = [
        "Need 5kg chicken",
        "low on milk",
        "2 boxes eggs",
        "5 litres milk and 2 boxes eggs",
        "we need eggs and milk",
    ]
    for msg in tests:
        print(json.dumps(parse_message(msg), indent=2))
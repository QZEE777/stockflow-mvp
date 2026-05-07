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

# --- Intent detection (applied to raw input before any cleaning) ---

# stock_count: staff reporting what's on hand
# matches: "only 3 left", "3 black label left", "5 remaining", "we have 3"
_STOCK_COUNT_PATTERN = re.compile(
    r'(\b\d+\b.*\b(left|remaining)\b|\bwe have\b.*\b\d+\b)',
    re.IGNORECASE
)

# low_stock: staff signalling a need but no specific quantity
_LOW_STOCK_PATTERN = re.compile(
    r'\b(low on|running low|almost out of|running out of)\b',
    re.IGNORECASE
)


def _detect_intent(raw_text: str) -> str:
    """Detect message intent from the original raw input before cleaning."""
    if _STOCK_COUNT_PATTERN.search(raw_text):
        return 'stock_count'
    if _LOW_STOCK_PATTERN.search(raw_text):
        return 'low_stock'
    return 'order_request'


# --- Text cleaning ---

_LEADING_FILLER = re.compile(
    r'^(need|low on|running low on|out of|we need|please get|get|order|i need|only)\s+',
    re.IGNORECASE
)

_TRAILING_FILLER = re.compile(
    r'\s+\b(left|remaining|needed|please|asap|urgently|urgent)\b.*$',
    re.IGNORECASE
)

_SEGMENT_LEADING = re.compile(
    r'^(more|some|a few|few|a bit of|any|some more|need more|need)\s+',
    re.IGNORECASE
)

_SEGMENT_TRAILING = re.compile(
    r'\s+\b(left|remaining|needed|please|asap|urgently|urgent)\b\s*$',
    re.IGNORECASE
)

_ITEM_PATTERN = re.compile(
    rf'(\d+(?:\.\d+)?)\s*({"|".join(UNITS)})?\s+([a-zA-Z][a-zA-Z\s]*?)(?=\s+\d+|$)',
    re.IGNORECASE
)


def _clean_segment(seg: str) -> str:
    seg = seg.strip().lower()
    seg = _SEGMENT_LEADING.sub('', seg)
    seg = _SEGMENT_TRAILING.sub('', seg)
    seg = re.sub(r'\b(and|plus|also)\b\s*$', '', seg)
    seg = re.sub(r'\s+', ' ', seg).strip()
    return seg


def _expand_variants(segments: list) -> list:
    """
    Expand variant patterns.
    e.g. ['sugar sachets white', 'brown'] -> ['sugar sachets white', 'sugar sachets brown']
    """
    result = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        words = seg.split()
        if (len(words) >= 2
                and i + 1 < len(segments)
                and len(segments[i + 1].split()) == 1):
            base = ' '.join(words[:-1])
            variant = segments[i + 1]
            result.append(seg)
            result.append(f"{base} {variant}")
            i += 2
        else:
            result.append(seg)
            i += 1
    return result


def _clean_quantity(qty: float):
    return int(qty) if qty == int(qty) else qty


def parse_message(raw_input: str) -> dict:
    # Detect intent from the original text before any cleaning
    intent = _detect_intent(raw_input)

    # Confidence floor for low_stock: quantity is assumed, not stated
    low_stock_confidence = 0.4

    text = raw_input.strip().lower()
    text = _LEADING_FILLER.sub('', text)
    text = _TRAILING_FILLER.sub('', text)
    text = text.replace(',', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    items = []

    for match in _ITEM_PATTERN.finditer(text):
        qty = float(match.group(1))
        raw_unit = match.group(2).lower() if match.group(2) else 'unit'
        item_name = match.group(3).strip().lower()
        item_name = re.sub(r'\b(and|plus|also)\b', '', item_name).strip()
        item_name = re.sub(r'\s+', ' ', item_name).strip()

        if not item_name:
            continue

        confidence = 0.9 if match.group(2) else 0.8
        if intent == 'low_stock':
            confidence = low_stock_confidence

        items.append({
            "name": item_name,
            "quantity": _clean_quantity(qty),
            "unit": _UNIT_NORM.get(raw_unit, raw_unit),
            "confidence": confidence,
            "intent": intent,
        })

    if not items and " and " in text:
        raw_parts = [p.strip() for p in text.split(" and ") if p.strip()]
        cleaned = [_clean_segment(p) for p in raw_parts]
        cleaned = [p for p in cleaned if p]
        expanded = _expand_variants(cleaned)
        for p in expanded:
            if p:
                confidence = low_stock_confidence if intent == 'low_stock' else 0.6
                items.append({
                    "name": p,
                    "quantity": 1,
                    "unit": "unit",
                    "confidence": confidence,
                    "intent": intent,
                })

    if not items:
        fallback = _clean_segment(text)
        confidence = low_stock_confidence if intent == 'low_stock' else 0.5
        items.append({
            "name": fallback or text,
            "quantity": 1,
            "unit": "unit",
            "confidence": confidence,
            "intent": intent,
        })

    return {
        "items": items,
        "raw_input": raw_input,
    }


if __name__ == "__main__":
    tests = [
        # (message, expected [(name, qty, unit, intent)])
        ("Need 5kg chicken",
         [("chicken", 5, "kg", "order_request")]),
        ("low on milk",
         [("milk", 1, "unit", "low_stock")]),
        ("2 boxes eggs",
         [("eggs", 2, "box", "order_request")]),
        ("5 litres milk and 2 boxes eggs",
         [("milk", 5, "l", "order_request"), ("eggs", 2, "box", "order_request")]),
        ("we need eggs and milk",
         [("eggs", 1, "unit", "order_request"), ("milk", 1, "unit", "order_request")]),
        ("Need more coffee and sugar sachets white and brown",
         [("coffee", 1, "unit", "order_request"),
          ("sugar sachets white", 1, "unit", "order_request"),
          ("sugar sachets brown", 1, "unit", "order_request")]),
        ("Only 3 black label left",
         [("black label", 3, "unit", "stock_count")]),
        ("Need 7 black labels",
         [("black labels", 7, "unit", "order_request")]),
        ("Low on Jamison",
         [("jamison", 1, "unit", "low_stock")]),
        ("order more coffee",
         [("coffee", 1, "unit", "order_request")]),
    ]

    passed = 0
    failed = 0
    for msg, expected in tests:
        result = parse_message(msg)
        actual = [(i["name"], i["quantity"], i["unit"], i["intent"]) for i in result["items"]]
        ok = actual == expected
        status = "PASS" if ok else "FAIL"
        print(f"{status} '{msg}'")
        if not ok:
            print(f"   Expected: {expected}")
            print(f"   Got:      {actual}")
            failed += 1
        else:
            passed += 1

    print(f"\n{passed}/{passed+failed} tests passed")

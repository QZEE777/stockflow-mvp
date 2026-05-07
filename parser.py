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

# Strip leading filler from the whole message
_LEADING_FILLER = re.compile(
    r'^(need|low on|running low on|out of|we need|please get|get|order|i need|only)\s+',
    re.IGNORECASE
)

# Strip trailing stock-state words from the whole message
_TRAILING_FILLER = re.compile(
    r'\s+\b(left|remaining|needed|please|asap|urgently|urgent)\b.*$',
    re.IGNORECASE
)

# Strip leading item-level filler from individual segments
_SEGMENT_LEADING = re.compile(
    r'^(more|some|a few|few|a bit of|any|some more|need more|need)\s+',
    re.IGNORECASE
)

# Strip trailing stock-state words from individual segments
_SEGMENT_TRAILING = re.compile(
    r'\s+\b(left|remaining|needed|please|asap|urgently|urgent)\b\s*$',
    re.IGNORECASE
)

_ITEM_PATTERN = re.compile(
    rf'(\d+(?:\.\d+)?)\s*({"|".join(UNITS)})?\s+([a-zA-Z][a-zA-Z\s]*?)(?=\s+\d+|$)',
    re.IGNORECASE
)


def _clean_segment(seg: str) -> str:
    """Clean an individual item segment — strip leading and trailing filler."""
    seg = seg.strip().lower()
    seg = _SEGMENT_LEADING.sub('', seg)
    seg = _SEGMENT_TRAILING.sub('', seg)
    seg = re.sub(r'\b(and|plus|also)\b\s*$', '', seg)
    seg = re.sub(r'\s+', ' ', seg).strip()
    return seg


def _expand_variants(segments: list) -> list:
    """
    Expand variant patterns where a single trailing word describes a variant
    of the previous multi-word item.

    Example:
      ['sugar sachets white', 'brown']
      → ['sugar sachets white', 'sugar sachets brown']

    Rule: if segment[i] has 2+ words and segment[i+1] is a single word,
    treat segment[i+1] as a variant — prepend segment[i]'s base (all words
    except the last) to it.
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

        items.append({
            "name": item_name,
            "quantity": _clean_quantity(qty),
            "unit": _UNIT_NORM.get(raw_unit, raw_unit),
            "confidence": 0.9 if match.group(2) else 0.8,
        })

    if not items and " and " in text:
        raw_parts = [p.strip() for p in text.split(" and ") if p.strip()]
        cleaned = [_clean_segment(p) for p in raw_parts]
        cleaned = [p for p in cleaned if p]
        expanded = _expand_variants(cleaned)
        for p in expanded:
            if p:
                items.append({
                    "name": p,
                    "quantity": 1,
                    "unit": "unit",
                    "confidence": 0.6,
                })

    if not items:
        fallback = _clean_segment(text)
        items.append({
            "name": fallback or text,
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
        ("Need 5kg chicken",
         [("chicken", 5, "kg")]),
        ("low on milk",
         [("milk", 1, "unit")]),
        ("2 boxes eggs",
         [("eggs", 2, "box")]),
        ("5 litres milk and 2 boxes eggs",
         [("milk", 5, "l"), ("eggs", 2, "box")]),
        ("we need eggs and milk",
         [("eggs", 1, "unit"), ("milk", 1, "unit")]),
        ("Need more coffee and sugar sachets white and brown",
         [("coffee", 1, "unit"), ("sugar sachets white", 1, "unit"), ("sugar sachets brown", 1, "unit")]),
        ("Only 3 black label left",
         [("black label", 3, "unit")]),
        ("Low on Jamison",
         [("jamison", 1, "unit")]),
        ("order more coffee",
         [("coffee", 1, "unit")]),
    ]

    passed = 0
    failed = 0
    for msg, expected in tests:
        result = parse_message(msg)
        actual = [(i["name"], i["quantity"], i["unit"]) for i in result["items"]]
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

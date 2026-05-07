import re

# Canonical name overrides — owner-configurable over time.
# Key = raw parsed name (lowercase), Value = canonical form.
ALIASES = {
    "black labels": "black label",
    "bl label": "black label",
    "bl": "black label",
    "jamieson": "jamison",
    "jamesons": "jamison",
    "jamiesons": "jamison",
    "linguinex2": "linguine",
    "linguine x2": "linguine",
    "black labels": "black label",
}

# Endings that should NOT have the trailing 's' stripped
_KEEP_S = {"ss", "us", "is", "as", "ys"}


def normalize_item(raw: str) -> str:
    """
    Return the canonical form of an item name for grouping and consolidation.

    Steps:
      1. Lowercase + collapse whitespace
      2. Alias map exact match (highest priority)
      3. Conservative singularization: strip trailing 's' on words > 5 chars
         unless the last two characters are in _KEEP_S

    This is deterministic and owner-tuneable via ALIASES.
    No AI involved.
    """
    name = raw.strip().lower()
    name = re.sub(r'\s+', ' ', name)

    if name in ALIASES:
        return ALIASES[name]

    words = name.split()
    normalized_words = []
    for word in words:
        if len(word) > 5 and word.endswith('s') and word[-2:] not in _KEEP_S:
            word = word[:-1]
        normalized_words.append(word)

    return ' '.join(normalized_words)


if __name__ == "__main__":
    tests = [
        ("black labels", "black label"),
        ("black label", "black label"),
        ("Black Labels", "black label"),
        ("BL label", "black label"),     # alias: bl label → black label
        ("mushrooms", "mushroom"),
        ("jalapeños", "jalapeño"),
        ("broccoli", "broccoli"),
        ("Jamison", "jamison"),
        ("jamesons", "jamison"),
        ("linguinex2", "linguine"),
        ("castle", "castle"),
        ("anchovies", "anchovie"),       # known limitation — alias if needed
    ]
    passed = 0
    for raw, expected in tests:
        result = normalize_item(raw)
        ok = result == expected
        print(f"{'PASS' if ok else 'FAIL'} '{raw}' -> '{result}' (expected '{expected}')")
        if ok:
            passed += 1
    print(f"\n{passed}/{len(tests)} passed")

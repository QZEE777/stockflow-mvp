from unittest.mock import patch, MagicMock
from parser import parse_message
from normalizer import normalize_item
from sheets_writer import write_parsed_result, HEADERS

BUSINESS_ID = "test_business"
USER_PHONE = "+27821234567"


def run_test(label, message, expect_sheet_write, expected_intent=None):
    parsed = parse_message(message)
    items = parsed["items"]

    # Verify intent on first item
    if expected_intent:
        actual_intent = items[0]["intent"]
        assert actual_intent == expected_intent, (
            f"[{label}] Intent mismatch: expected {expected_intent}, got {actual_intent}"
        )

    # Simulate the api.py routing logic (normalize + filter)
    for item in items:
        item["normalized_item"] = normalize_item(item["name"])
    items_to_write = [i for i in items if i.get("intent") != "stock_count"]

    mock_sheet = MagicMock()
    with patch("sheets_writer._get_sheet", return_value=mock_sheet):
        if items_to_write:
            write_parsed_result(
                {"items": items_to_write, "raw_input": parsed["raw_input"]},
                BUSINESS_ID, USER_PHONE
            )

    did_write = mock_sheet.append_row.called
    assert did_write == expect_sheet_write, (
        f"[{label}] Sheet write expected={expect_sheet_write}, got={did_write}"
    )

    print(f"PASS '{label}'")
    if did_write:
        row = mock_sheet.append_row.call_args[0][0]
        for header, value in zip(HEADERS, row):
            print(f"  {header}: {value}")
    else:
        print(f"  (no sheet write — {items[0]['intent']})")


if __name__ == "__main__":
    run_test(
        label="order_request — specific quantity",
        message="Need 5kg chicken",
        expect_sheet_write=True,
        expected_intent="order_request",
    )
    print()
    run_test(
        label="order_request — Need 7 black labels",
        message="Need 7 black labels",
        expect_sheet_write=True,
        expected_intent="order_request",
    )
    print()
    run_test(
        label="stock_count — Only 3 black label left",
        message="Only 3 black label left",
        expect_sheet_write=False,
        expected_intent="stock_count",
    )
    print()
    run_test(
        label="low_stock — Low on Jamison",
        message="Low on Jamison",
        expect_sheet_write=True,
        expected_intent="low_stock",
    )

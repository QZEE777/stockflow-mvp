from unittest.mock import patch, MagicMock
from parser import parse_message
from sheets_writer import write_parsed_result, HEADERS

SAMPLE_MESSAGE = "Need 5kg chicken"
BUSINESS_ID = "test_business"
USER_PHONE = "+27821234567"

def test_pipeline():
    parsed = parse_message(SAMPLE_MESSAGE)
    print("Parsed result:")
    for k, v in parsed.items():
        print(f"  {k}: {v}")

    mock_sheet = MagicMock()
    with patch("sheets_writer._get_sheet", return_value=mock_sheet):
        write_parsed_result(parsed, BUSINESS_ID, USER_PHONE)

    written_row = mock_sheet.append_row.call_args[0][0]
    print("\nRow that would be written to Google Sheets:")
    for header, value in zip(HEADERS, written_row):
        print(f"  {header}: {value}")

if __name__ == "__main__":
    test_pipeline()

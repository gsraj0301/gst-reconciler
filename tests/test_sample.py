import json
from pathlib import Path

from gst_reconciler.matcher import get_summary, match_rows
from gst_reconciler.parser import parse_gstr2b_file, parse_tally_file

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample"


def test_sample_matches_expected_summary():
    tally_rows = parse_tally_file(str(SAMPLE_DIR / "tally-purchases-apr-2025.xlsx"))
    gst_rows = parse_gstr2b_file(str(SAMPLE_DIR / "gstr2b-apr-2025.xlsx"))
    expected = json.loads((SAMPLE_DIR / "expected_summary.json").read_text())

    results = match_rows(tally_rows, gst_rows)

    assert len(tally_rows) == expected["tally_rows"]
    assert len(gst_rows) == expected["gstr2b_rows"]
    assert len(results) == expected["result_rows"]
    assert get_summary(results) == expected["summary"]

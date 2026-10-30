from openpyxl import Workbook, load_workbook

from gst_reconciler.matcher import MatchResult, get_summary
from gst_reconciler.writer import write_reconciliation_report


def _write_input(path):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "B2B"
    worksheet["A1"] = "original"
    workbook.create_sheet("B2B-CDNR")
    workbook.save(path)


def test_writer_adds_report_sheet_and_preserves_original_sheets(
    tmp_path, make_tally, make_gst
):
    input_path = tmp_path / "gstr2b.xlsx"
    output_path = tmp_path / "gstr2b-reconciled.xlsx"
    _write_input(input_path)

    results = [
        MatchResult(
            status="Matched",
            tally_row=make_tally(row_index=0),
            gst_row=make_gst(row_index=0),
        ),
        MatchResult(
            status="Invoice Value Mismatch",
            tally_row=make_tally(row_index=1),
            gst_row=make_gst(row_index=1),
        ),
        MatchResult(
            status="In Tally but not in GSTR-2B",
            tally_row=make_tally(row_index=2),
            gst_row=None,
        ),
        MatchResult(
            status="In GSTR-2B but not in Tally",
            tally_row=None,
            gst_row=make_gst(row_index=2),
        ),
    ]

    write_reconciliation_report(
        str(input_path), str(output_path), results, get_summary(results)
    )

    output = load_workbook(output_path)
    source = load_workbook(input_path)

    assert output.sheetnames[0] == "Reconciliation Report"
    assert output.sheetnames == ["Reconciliation Report", "B2B", "B2B-CDNR"]
    assert source.sheetnames == ["B2B", "B2B-CDNR"]
    assert output["Reconciliation Report"]["A1"].value == "Status"
    assert output["B2B"]["A1"].value == "original"
    assert any(
        cell.value == "SUMMARY"
        for row in output["Reconciliation Report"].iter_rows()
        for cell in row
    )


def test_writer_colors_matched_and_mismatch_rows(tmp_path, make_tally, make_gst):
    input_path = tmp_path / "gstr2b.xlsx"
    output_path = tmp_path / "gstr2b-reconciled.xlsx"
    _write_input(input_path)

    results = [
        MatchResult(
            status="Matched",
            tally_row=make_tally(row_index=0),
            gst_row=make_gst(row_index=0),
        ),
        MatchResult(
            status="Taxable Value Mismatch",
            tally_row=make_tally(row_index=1),
            gst_row=make_gst(row_index=1),
        ),
    ]

    write_reconciliation_report(
        str(input_path), str(output_path), results, get_summary(results)
    )

    worksheet = load_workbook(output_path)["Reconciliation Report"]

    assert worksheet["A2"].value == "Matched"
    assert worksheet["A2"].fill.start_color.rgb == "00C6EFCE"
    assert worksheet["A3"].value == "Taxable Value Mismatch"
    assert worksheet["A3"].fill.start_color.rgb == "00FFC7CE"

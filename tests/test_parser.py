from openpyxl import Workbook

from gst_reconciler.parser import parse_gstr2b_file, parse_tally_file


TALLY_HEADERS = [
    "Date",
    "Particulars",
    "Voucher Type",
    "Voucher No.",
    "Supplier Invoice No.",
    "Supplier Invoice Date",
    "GSTIN/UIN",
    "Value",
    "Gross Total",
    "Taxable Value",
    "IGST Input",
    "CGST Input",
    "SGST Input",
]


def _write_tally(path, rows, sheet_name="PURCHASE REGISTER"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(["Dummy Company Pvt Ltd"])
    worksheet.append(TALLY_HEADERS)
    for row in rows:
        worksheet.append(row)
    workbook.save(path)


def test_parse_tally_with_alternate_sheet_and_headers(tmp_path):
    path = tmp_path / "tally.xlsx"
    _write_tally(
        path,
        [
            [
                "01/04/2025",
                "Acme Supplies",
                "Purchase",
                "V-001",
                "INV-001",
                "01/04/2025",
                "27AAAAA0000A1Z5",
                1000,
                1180,
                1000,
                0,
                90,
                90,
            ]
        ],
    )

    rows = parse_tally_file(str(path))

    assert len(rows) == 1
    assert rows[0].gstin == "27AAAAA0000A1Z5"
    assert rows[0].particulars == "ACME SUPPLIES"
    assert rows[0].voucher_ref_no == "INV001"
    assert rows[0].taxable_value == 1000
    assert rows[0].gross_total == 1180
    assert rows[0].cgst == 90
    assert rows[0].sgst == 90


def test_parse_tally_skips_rows_without_gstin(tmp_path):
    path = tmp_path / "tally-missing-gstin.xlsx"
    _write_tally(
        path,
        [
            [
                "01/04/2025",
                "Acme Supplies",
                "Purchase",
                "V-001",
                "INV-001",
                "01/04/2025",
                "27AAAAA0000A1Z5",
                1000,
                1180,
                1000,
                0,
                90,
                90,
            ],
            [
                "02/04/2025",
                "Missing Gstin Party",
                "Purchase",
                "V-002",
                "INV-002",
                "02/04/2025",
                None,
                500,
                590,
                500,
                0,
                45,
                45,
            ],
        ],
    )

    rows = parse_tally_file(str(path))

    assert len(rows) == 1
    assert rows[0].voucher_ref_no == "INV001"


def test_parse_gstr2b_with_merged_two_row_headers(tmp_path):
    path = tmp_path / "gstr2b.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "B2B"

    worksheet["A1"] = "Taxable inward supplies"
    worksheet["A5"] = "GSTIN of supplier"
    worksheet["B5"] = "Trade/Legal name"
    worksheet["C5"] = "Invoice Details"
    worksheet.merge_cells("C5:F5")
    worksheet["G5"] = "Place of supply"
    worksheet["H5"] = "Supply Attract Reverse Charge"
    worksheet["I5"] = "Taxable Value (₹)"
    worksheet["J5"] = "Tax Amount"
    worksheet.merge_cells("J5:M5")

    worksheet["C6"] = "Invoice number"
    worksheet["D6"] = "Invoice type"
    worksheet["E6"] = "Invoice Date"
    worksheet["F6"] = "Invoice Value(₹)"
    worksheet["J6"] = "Integrated Tax(₹)"
    worksheet["K6"] = "Central Tax(₹)"
    worksheet["L6"] = "State/UT Tax(₹)"
    worksheet["M6"] = "Cess(₹)"

    worksheet.append(
        [
            "27AAAAA0000A1Z5",
            "Acme Supplies",
            "INV-001",
            "Regular",
            "01/04/2025",
            1180,
            "Maharashtra",
            "No",
            1000,
            0,
            90,
            90,
            0,
        ]
    )
    workbook.save(path)

    rows = parse_gstr2b_file(str(path))

    assert len(rows) == 1
    assert rows[0].gstin == "27AAAAA0000A1Z5"
    assert rows[0].trade_name == "ACME SUPPLIES"
    assert rows[0].invoice_no == "INV001"
    assert rows[0].invoice_value == 1180
    assert rows[0].taxable_value == 1000
    assert rows[0].cgst == 90
    assert rows[0].sgst == 90

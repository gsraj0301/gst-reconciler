import pandas as pd
import pytest

from gst_reconciler.parser import GstRow, TallyRow


@pytest.fixture
def make_tally():
    def _make(
        row_index=0,
        gstin="27AAAAA0000A1Z5",
        invoice_no="INV001",
        party="ACME SUPPLIES",
        taxable_value=1000.0,
        gross_total=1180.0,
        igst=0.0,
        cgst=90.0,
        sgst=90.0,
    ):
        return TallyRow(
            date=pd.Timestamp("2025-04-01"),
            particulars=party,
            voucher_type="Purchase",
            voucher_no=f"V-{row_index}",
            voucher_ref_no=invoice_no,
            voucher_ref_date=pd.Timestamp("2025-04-01"),
            gstin=gstin,
            value=taxable_value,
            gross_total=gross_total,
            taxable_value=taxable_value,
            cgst=cgst,
            sgst=sgst,
            igst=igst,
            row_index=row_index,
        )

    return _make


@pytest.fixture
def make_gst():
    def _make(
        row_index=0,
        gstin="27AAAAA0000A1Z5",
        invoice_no="INV001",
        party="ACME SUPPLIES",
        taxable_value=1000.0,
        invoice_value=1180.0,
        igst=0.0,
        cgst=90.0,
        sgst=90.0,
    ):
        return GstRow(
            gstin=gstin,
            trade_name=party,
            invoice_no=invoice_no,
            invoice_type="Regular",
            invoice_date=pd.Timestamp("2025-04-01"),
            invoice_value=invoice_value,
            place_of_supply="Maharashtra",
            reverse_charge="No",
            taxable_value=taxable_value,
            igst=igst,
            cgst=cgst,
            sgst=sgst,
            cess=0.0,
            row_index=row_index,
        )

    return _make

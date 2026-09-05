import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .matcher import MatchResult


HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
MISMATCH_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
MATCHED_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
TALLY_ONLY_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
GST_ONLY_FILL = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)


def get_status_fill(status: str) -> PatternFill:
    if status == "Matched":
        return MATCHED_FILL
    elif "In Tally but not in GSTR-2B" in status:
        return TALLY_ONLY_FILL
    elif "In GSTR-2B but not in Tally" in status:
        return GST_ONLY_FILL
    elif "Duplicate" in status:
        return PatternFill(start_color="F4B084", end_color="F4B084", fill_type="solid")
    else:
        return MISMATCH_FILL


def write_reconciliation_report(gst_filepath: str, output_filepath: str, results: list[MatchResult], summary: dict):
    wb = openpyxl.load_workbook(gst_filepath)
    
    if "Reconciliation Report" in wb.sheetnames:
        wb.remove(wb["Reconciliation Report"])
    
    ws = wb.create_sheet("Reconciliation Report", 0)
    
    headers = [
        "Status",
        "GSTIN",
        "Party Name",
        "Invoice No",
        "Invoice Date",
        "Tally Invoice Value",
        "GSTR-2B Invoice Value",
        "Invoice Value Diff",
        "Tally Taxable Value",
        "GSTR-2B Taxable Value",
        "Taxable Value Diff",
        "Tally IGST",
        "GSTR-2B IGST",
        "IGST Diff",
        "Tally CGST",
        "GSTR-2B CGST",
        "CGST Diff",
        "Tally SGST",
        "GSTR-2B SGST",
        "SGST Diff",
        "Tally Row",
        "GSTR-2B Row"
    ]
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = THIN_BORDER
    
    for row_idx, result in enumerate(results, 2):
        t = result.tally_row
        g = result.gst_row
        
        gstin = t.gstin if t else (g.gstin if g else "")
        party = t.particulars if t else (g.trade_name if g else "")
        inv_no = t.voucher_ref_no if t else (g.invoice_no if g else "")
        inv_date = t.voucher_ref_date if t else (g.invoice_date if g else None)
        
        tally_inv_val = t.gross_total if t else 0.0
        gst_inv_val = g.invoice_value if g else 0.0
        tally_tax_val = t.taxable_value if t else 0.0
        gst_tax_val = g.taxable_value if g else 0.0
        tally_igst = t.igst if t else 0.0
        gst_igst = g.igst if g else 0.0
        tally_cgst = t.cgst if t else 0.0
        gst_cgst = g.cgst if g else 0.0
        tally_sgst = t.sgst if t else 0.0
        gst_sgst = g.sgst if g else 0.0
        
        values = [
            result.status,
            gstin,
            party,
            inv_no,
            inv_date.strftime("%d/%m/%Y") if inv_date and not pd.isna(inv_date) else "",
            tally_inv_val,
            gst_inv_val,
            result.invoice_value_diff,
            tally_tax_val,
            gst_tax_val,
            result.taxable_value_diff,
            tally_igst,
            gst_igst,
            result.igst_diff,
            tally_cgst,
            gst_cgst,
            result.cgst_diff,
            tally_sgst,
            gst_sgst,
            result.sgst_diff,
            t.row_index if t else "",
            g.row_index if g else ""
        ]
        
        fill = get_status_fill(result.status)
        
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.fill = fill
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal='center' if col_idx > 1 else 'left')
            if col_idx >= 6 and isinstance(val, (int, float)):
                cell.number_format = '#,##0.00'
    
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(results) + 1}"
    
    column_widths = {
        'A': 35, 'B': 18, 'C': 35, 'D': 20, 'E': 14,
        'F': 18, 'G': 18, 'H': 16, 'I': 18, 'J': 18, 'K': 16,
        'L': 14, 'M': 14, 'N': 12, 'O': 14, 'P': 14, 'Q': 12,
        'R': 14, 'S': 14, 'T': 12, 'U': 10, 'V': 10
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    ws.freeze_panes = "A2"
    
    summary_row = len(results) + 3
    ws.cell(row=summary_row, column=1, value="SUMMARY").font = Font(bold=True, size=12)
    summary_row += 1
    
    for cat, count in summary.items():
        ws.cell(row=summary_row, column=1, value=cat).font = Font(bold=True)
        ws.cell(row=summary_row, column=2, value=count).alignment = Alignment(horizontal='center')
        ws.cell(row=summary_row, column=2).border = THIN_BORDER
        ws.cell(row=summary_row, column=1).border = THIN_BORDER
        summary_row += 1
    
    wb.save(output_filepath)
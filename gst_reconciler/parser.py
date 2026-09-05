import re
import pandas as pd
from openpyxl import load_workbook
from dataclasses import dataclass
from typing import Optional


@dataclass
class TallyRow:
    date: pd.Timestamp
    particulars: str
    voucher_type: str
    voucher_no: str
    voucher_ref_no: str
    voucher_ref_date: pd.Timestamp
    gstin: str
    value: float
    gross_total: float
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    row_index: int


@dataclass
class GstRow:
    gstin: str
    trade_name: str
    invoice_no: str
    invoice_type: str
    invoice_date: pd.Timestamp
    invoice_value: float
    place_of_supply: str
    reverse_charge: str
    taxable_value: float
    igst: float
    cgst: float
    sgst: float
    cess: float
    row_index: int


def clean_gstin(gstin: str) -> str:
    if pd.isna(gstin):
        return ""
    return re.sub(r'[\s\-]', '', str(gstin)).upper()


def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    return str(text).strip().upper()


def clean_invoice_no(inv_no: str) -> str:
    if pd.isna(inv_no):
        return ""
    return re.sub(r'[\s\-\/]', '', str(inv_no)).upper()


def parse_date(val) -> pd.Timestamp:
    if pd.isna(val):
        return pd.NaT
    if isinstance(val, pd.Timestamp):
        return val
    try:
        return pd.to_datetime(val, dayfirst=True)
    except Exception:
        try:
            return pd.to_datetime(val)
        except Exception:
            return pd.NaT


def parse_float(val) -> float:
    if pd.isna(val):
        return 0.0
    try:
        return float(val)
    except Exception:
        try:
            return float(str(val).replace(',', ''))
        except Exception:
            return 0.0


def find_header_row(df: pd.DataFrame, keywords: list, min_matches: int = None) -> int:
    if min_matches is None:
        min_matches = len(keywords)
    best_row = -1
    best_count = 0
    for i in range(min(20, df.shape[0])):
        row_text = ' '.join(str(df.iloc[i, j]) for j in range(df.shape[1]) if pd.notna(df.iloc[i, j]))
        row_upper = row_text.upper()
        count = sum(1 for kw in keywords if kw.upper() in row_upper)
        if count >= min_matches and count > best_count:
            best_row = i
            best_count = count
            if count == len(keywords):
                break
    return best_row


def validate_col_map(col_map: dict, df: pd.DataFrame, file_label: str):
    max_col = df.shape[1]
    missing = []
    for field, idx in col_map.items():
        if idx is None or idx >= max_col:
            missing.append(f"  '{field}' -> column index {idx} (file has {max_col} columns)")
    if missing:
        found_headers = []
        for j in range(df.shape[1]):
            for i in range(min(10, df.shape[0])):
                val = df.iloc[i, j]
                if pd.notna(val):
                    found_headers.append(f"  col {j}: '{val}' (row {i})")
                    break
        raise ValueError(
            f"{file_label}: Some expected columns were not found in the file.\n"
            f"Missing/out-of-bounds columns:\n" + '\n'.join(missing) + "\n"
            f"Headers detected in file:\n" + '\n'.join(found_headers)
        )


def _get_merged_cell_headers(filepath: str, sheet_name: str):
    """Use openpyxl to read merged cells and build a two-row header map.

    GSTR-2B has a two-row header structure:
      Row 5 (1-indexed): main headers with merged cells like 'Invoice Details' (C5:F5)
      Row 6 (1-indexed): sub-headers under merged ranges (Invoice number, Invoice type, etc.)

    Returns (headers dict, header_row_0indexed, data_start_row_0indexed).
    """
    wb = load_workbook(filepath, data_only=True)
    ws = wb[sheet_name]

    merged_ranges = list(ws.merged_cells.ranges)
    wb.close()

    # Find all rows that contain header-like content (text values)
    header_rows = []
    max_scan = min(15, ws.max_row or 10)
    for row_idx in range(1, max_scan + 1):
        row_vals = []
        for cell in ws[row_idx]:
            if cell.value is not None:
                row_vals.append((cell.column - 1, str(cell.value).strip()))
        if row_vals:
            header_rows.append((row_idx - 1, row_vals))  # convert to 0-indexed

    # Find the main header row (has 'GSTIN of supplier' or 'GSTIN OF SUPPLIER')
    # and the sub-header row (has 'Invoice number' or 'INVOICE NUMBER')
    main_row_idx = -1
    sub_row_idx = -1
    for row_0idx, cells in header_rows:
        cell_text = ' '.join(val for _, val in cells).upper()
        if 'GSTIN OF SUPPLIER' in cell_text or 'GSTIN' in cell_text:
            main_row_idx = row_0idx
        if 'INVOICE NUMBER' in cell_text or 'CENTRAL TAX' in cell_text:
            sub_row_idx = row_0idx

    if main_row_idx == -1:
        main_row_idx = 4
    if sub_row_idx == -1:
        sub_row_idx = main_row_idx + 1

    # Build merged cell mapping: col -> merged_label
    merged_map = {}  # col_index -> (label, start_col, end_col)
    for mc in merged_ranges:
        min_col = mc.min_col - 1  # 0-indexed
        max_col = mc.max_col - 1
        min_row = mc.min_row - 1
        max_row = mc.max_row - 1
        label_val = ws.cell(row=mc.min_row, column=mc.min_col).value
        if label_val and max_col > min_col:
            # This is a horizontally merged cell spanning multiple columns
            for c in range(min_col, max_col + 1):
                merged_map[c] = str(label_val).strip().upper()

    # Build combined headers from both rows
    headers = {}

    # Read main row (row 5) — these are the top-level headers
    for j in range(ws.max_column or 21):
        cell = ws.cell(row=main_row_idx + 1, column=j + 1)  # 1-indexed
        val = cell.value
        if val is not None:
            headers[str(val).strip().upper()] = j

    # Read sub-row (row 6) — these fill in under merged ranges
    for j in range(ws.max_column or 21):
        cell = ws.cell(row=sub_row_idx + 1, column=j + 1)
        val = cell.value
        if val is not None:
            key = str(val).strip().upper()
            if key not in headers:
                headers[key] = j

    # Data starts after the last header row
    data_start = max(main_row_idx, sub_row_idx) + 1
    return headers, main_row_idx, data_start


def _normalize_header(name: str) -> str:
    """Normalize a header name for matching: uppercase, strip, remove extra spaces."""
    s = str(name).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    return s


def _find_header_in_dict(headers: dict, candidates: list[str], exact=False):
    """Search headers dict for any of the candidate names. Returns column index or None."""
    for candidate in candidates:
        normalized = _normalize_header(candidate)
        if exact:
            if normalized in headers:
                return headers[normalized]
        else:
            for key, idx in headers.items():
                if normalized in key or key in normalized:
                    return idx
    return None


def parse_gstr2b_file(filepath: str) -> list[GstRow]:
    df = pd.read_excel(filepath, sheet_name='B2B', header=None)

    headers, header_row, data_start = _get_merged_cell_headers(filepath, 'B2B')

    # Build col_map from the combined headers
    col_map = {
        'gstin': _find_header_in_dict(headers, ['GSTIN OF SUPPLIER', 'GSTIN'], exact=True),
        'trade_name': _find_header_in_dict(headers, ['TRADE/LEGAL NAME', 'TRADE NAME', 'LEGAL NAME'], exact=True),
        'invoice_no': _find_header_in_dict(headers, ['INVOICE NUMBER', 'INVOICE NO'], exact=True),
        'invoice_type': _find_header_in_dict(headers, ['INVOICE TYPE'], exact=True),
        'invoice_date': _find_header_in_dict(headers, ['INVOICE DATE'], exact=True),
        'invoice_value': _find_header_in_dict(headers, ['INVOICE VALUE(₹)', 'INVOICE VALUE', 'INVOICE VALUE (₹)'], exact=True),
        'place_of_supply': _find_header_in_dict(headers, ['PLACE OF SUPPLY'], exact=True),
        'reverse_charge': _find_header_in_dict(headers, ['SUPPLY ATTRACT REVERSE CHARGE', 'REVERSE CHARGE'], exact=True),
        'taxable_value': _find_header_in_dict(headers, ['TAXABLE VALUE (₹)', 'TAXABLE VALUE(₹)', 'TAXABLE VALUE'], exact=True),
        'igst': _find_header_in_dict(headers, ['INTEGRATED TAX(₹)', 'INTEGRATED TAX (₹)', 'INTEGRATED TAX'], exact=True),
        'cgst': _find_header_in_dict(headers, ['CENTRAL TAX(₹)', 'CENTRAL TAX (₹)', 'CENTRAL TAX'], exact=True),
        'sgst': _find_header_in_dict(headers, ['STATE/UT TAX(₹)', 'STATE/UT TAX (₹)', 'STATE/UT TAX'], exact=True),
        'cess': _find_header_in_dict(headers, ['CESS(₹)', 'CESS (₹)', 'CESS'], exact=True),
    }

    # Fallback for any fields not found: try fuzzy match
    for field, val in col_map.items():
        if val is None:
            col_map[field] = _find_header_in_dict(headers, [field.replace('_', ' ')], exact=False)

    # Final fallback: use sequential defaults only if nothing else works
    defaults = {
        'gstin': 0, 'trade_name': 1, 'invoice_no': 2, 'invoice_type': 3,
        'invoice_date': 4, 'invoice_value': 5, 'place_of_supply': 6,
        'reverse_charge': 7, 'taxable_value': 8, 'igst': 9,
        'cgst': 10, 'sgst': 11, 'cess': 12,
    }
    for field in col_map:
        if col_map[field] is None:
            col_map[field] = defaults.get(field, 0)

    validate_col_map(col_map, df, "GSTR-2B file")

    rows = []
    for i in range(data_start, df.shape[0]):
        if pd.isna(df.iloc[i, col_map['gstin']]) and pd.isna(df.iloc[i, col_map['invoice_no']]):
            continue

        gstin = clean_gstin(df.iloc[i, col_map['gstin']])
        if not gstin:
            continue

        row = GstRow(
            gstin=gstin,
            trade_name=clean_text(df.iloc[i, col_map['trade_name']]),
            invoice_no=clean_invoice_no(df.iloc[i, col_map['invoice_no']]),
            invoice_type=str(df.iloc[i, col_map['invoice_type']]) if pd.notna(df.iloc[i, col_map['invoice_type']]) else '',
            invoice_date=parse_date(df.iloc[i, col_map['invoice_date']]),
            invoice_value=parse_float(df.iloc[i, col_map['invoice_value']]),
            place_of_supply=str(df.iloc[i, col_map['place_of_supply']]) if pd.notna(df.iloc[i, col_map['place_of_supply']]) else '',
            reverse_charge=str(df.iloc[i, col_map['reverse_charge']]) if pd.notna(df.iloc[i, col_map['reverse_charge']]) else '',
            taxable_value=parse_float(df.iloc[i, col_map['taxable_value']]),
            igst=parse_float(df.iloc[i, col_map['igst']]),
            cgst=parse_float(df.iloc[i, col_map['cgst']]),
            sgst=parse_float(df.iloc[i, col_map['sgst']]),
            cess=parse_float(df.iloc[i, col_map['cess']]),
            row_index=i
        )
        rows.append(row)

    return rows


def _resolve_sheet_name(filepath: str, candidates: list[str]) -> str:
    """Try sheet names in order, return the first one that exists."""
    xls = pd.ExcelFile(filepath)
    available = [s.strip() for s in xls.sheet_names]
    xls.close()
    for name in candidates:
        for actual in available:
            if actual.lower() == name.lower():
                return actual
    raise ValueError(
        f"No matching sheet found in file.\n"
        f"Tried: {candidates}\n"
        f"Available sheets: {available}"
    )


def parse_tally_file(filepath: str) -> list[TallyRow]:
    sheet_name = _resolve_sheet_name(filepath, ['CGST Input', 'PURCHASE REGISTER', 'Purchase Register', 'Purchase register'])
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

    # Relaxed header detection: try all 3 keywords, then 2 of 3
    header_row = find_header_row(df, ['GSTIN', 'VOUCHER REF', 'PARTICULARS'])
    if header_row == -1:
        header_row = find_header_row(df, ['GSTIN', 'PARTICULARS'], min_matches=2)
    if header_row == -1:
        header_row = find_header_row(df, ['GSTIN', 'PARTICULARS', 'DATE', 'VOUCHER', 'TAXABLE VALUE', 'CGST', 'SGST'], min_matches=4)
    if header_row == -1:
        header_row = find_header_row(df, ['GSTIN', 'DATE'], min_matches=2)

    if header_row == -1:
        raise ValueError(
            f"Could not detect header row in sheet '{sheet_name}'.\n"
            f"Expected columns like: GSTIN, Particulars, Voucher, Taxable Value, CGST, SGST.\n"
            f"File shape: {df.shape[0]} rows x {df.shape[1]} columns."
        )

    headers = {}
    for j in range(df.shape[1]):
        val = df.iloc[header_row, j]
        if pd.notna(val):
            headers[_normalize_header(str(val))] = j

    # Column alias map: primary name -> list of acceptable aliases
    field_aliases = {
        'date': ['DATE'],
        'particulars': ['PARTICULARS'],
        'voucher_type': ['VOUCHER TYPE', 'VOUCHER TYPE.'],
        'voucher_no': ['VOUCHER NO.', 'VOUCHER NO', 'VOUCHER NUMBER'],
        'voucher_ref_no': ['VOUCHER REF. NO.', 'VOUCHER REF. NO', 'VOUCHER REF NO.',
                           'SUPPLIER INVOICE NO.', 'SUPPLIER INVOICE NO', 'SUPPLIER INVOICE NUMBER',
                           'INVOICE NO.', 'INVOICE NO', 'INVOICE NUMBER',
                           'REF. NO.', 'REF NO.'],
        'voucher_ref_date': ['VOUCHER REF. DATE', 'VOUCHER REF. DATE', 'VOUCHER REF DATE',
                             'SUPPLIER INVOICE DATE', 'INVOICE DATE',
                             'REF. DATE', 'REF DATE'],
        'gstin': ['GSTIN/UIN', 'GSTIN/UIN', 'GSTIN'],
        'value': ['VALUE', 'INVOICE VALUE', 'VOUCHER VALUE'],
        'gross_total': ['GROSS TOTAL', 'GROSS TOTAL', 'GROSS AMOUNT'],
        'taxable_value': ['TAXABLE VALUE', 'TAXABLE VALUE', 'TAXABLE AMOUNT'],
        'cgst': ['CGST INPUT', 'CGST', 'CENTRAL TAX', 'CENTRAL TAX INPUT'],
        'sgst': ['SGST INPUT', 'SGST', 'STATE/UT TAX', 'STATE TAX', 'STATE/UT TAX INPUT'],
        'igst': ['IGST INPUT', 'IGST', 'INTEGRATED TAX', 'INTEGRATED TAX INPUT'],
    }

    col_map = {}
    for field, aliases in field_aliases.items():
        idx = None
        for alias in aliases:
            normalized = _normalize_header(alias)
            if normalized in headers:
                idx = headers[normalized]
                break
        col_map[field] = idx

    # Validate bounds — some fields are optional (voucher_type, value may not exist)
    optional_fields = {'voucher_type', 'value'}
    max_col = df.shape[1]
    missing_required = []
    for field, idx in col_map.items():
        if idx is not None and idx >= max_col:
            if field in optional_fields:
                col_map[field] = None  # will use defaults below
            else:
                missing_required.append(field)
        elif idx is None and field not in optional_fields:
            missing_required.append(field)
    if missing_required:
        found_headers = []
        for name, idx in sorted(headers.items(), key=lambda x: x[1]):
            found_headers.append(f"  col {idx}: '{name}'")
        raise ValueError(
            f"Tally file: Could not find required columns: {missing_required}\n"
            f"Detected headers in sheet '{sheet_name}' (row {header_row}):\n"
            + '\n'.join(found_headers) + f"\nFile has {max_col} columns."
        )

    rows = []
    for i in range(header_row + 1, df.shape[0]):
        if pd.isna(df.iloc[i, col_map['particulars']]) and pd.isna(df.iloc[i, col_map['gstin']]):
            continue

        gstin = clean_gstin(df.iloc[i, col_map['gstin']])
        if not gstin:
            continue

        def _safe_str(field):
            idx = col_map[field]
            if idx is None or pd.isna(df.iloc[i, idx]):
                return ''
            return str(df.iloc[i, idx])

        def _safe_float(field):
            idx = col_map[field]
            if idx is None:
                return 0.0
            return parse_float(df.iloc[i, idx])

        row = TallyRow(
            date=parse_date(df.iloc[i, col_map['date']]),
            particulars=clean_text(df.iloc[i, col_map['particulars']]),
            voucher_type=_safe_str('voucher_type'),
            voucher_no=_safe_str('voucher_no'),
            voucher_ref_no=clean_invoice_no(df.iloc[i, col_map['voucher_ref_no']]),
            voucher_ref_date=parse_date(df.iloc[i, col_map['voucher_ref_date']]),
            gstin=gstin,
            value=_safe_float('value'),
            gross_total=_safe_float('gross_total'),
            taxable_value=parse_float(df.iloc[i, col_map['taxable_value']]),
            cgst=parse_float(df.iloc[i, col_map['cgst']]),
            sgst=parse_float(df.iloc[i, col_map['sgst']]),
            igst=parse_float(df.iloc[i, col_map['igst']]),
            row_index=i
        )
        rows.append(row)

    return rows

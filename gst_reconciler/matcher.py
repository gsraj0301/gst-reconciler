from dataclasses import dataclass
from typing import Optional
from .parser import TallyRow, GstRow


@dataclass
class MatchResult:
    status: str
    tally_row: Optional[TallyRow]
    gst_row: Optional[GstRow]
    invoice_value_diff: float = 0.0
    taxable_value_diff: float = 0.0
    igst_diff: float = 0.0
    cgst_diff: float = 0.0
    sgst_diff: float = 0.0


THRESHOLD = 10.0

MATCHED_STATUSES = (
    "Matched",
    "Matched (Amount Verified)",
)

VALUE_MISMATCH_CATEGORIES = (
    "Invoice Value Mismatch",
    "Taxable Value Mismatch",
    "Integrated Tax Mismatch",
    "Central Tax Mismatch",
    "State/UT Tax Mismatch",
)

MISMATCH_CATEGORIES = (
    "In Tally but not in GSTR-2B",
    "In GSTR-2B but not in Tally",
    *VALUE_MISMATCH_CATEGORIES,
    "Duplicate in Tally",
    "Duplicate in GSTR-2B",
)

ALL_STATUSES = MATCHED_STATUSES + MISMATCH_CATEGORIES


def make_key(gstin: str, invoice_no: str, party_name: str) -> tuple:
    return (gstin, invoice_no, party_name)


def compute_diffs(t_row: TallyRow, g_row: GstRow) -> tuple:
    """Compute all differences between tally and GST rows."""
    return (
        abs(t_row.gross_total - g_row.invoice_value),
        abs(t_row.taxable_value - g_row.taxable_value),
        abs(t_row.igst - g_row.igst),
        abs(t_row.cgst - g_row.cgst),
        abs(t_row.sgst - g_row.sgst)
    )


def get_mismatch_status(inv_diff: float, tax_diff: float, igst_diff: float,
                        cgst_diff: float, sgst_diff: float) -> str:
    """Get status string based on differences vs threshold."""
    mismatches = []
    if inv_diff > THRESHOLD:
        mismatches.append("Invoice Value Mismatch")
    if tax_diff > THRESHOLD:
        mismatches.append("Taxable Value Mismatch")
    if igst_diff > THRESHOLD:
        mismatches.append("Integrated Tax Mismatch")
    if cgst_diff > THRESHOLD:
        mismatches.append("Central Tax Mismatch")
    if sgst_diff > THRESHOLD:
        mismatches.append("State/UT Tax Mismatch")

    return "; ".join(mismatches) if mismatches else "Matched"


def append_pair_result(results: list[MatchResult], t_row: TallyRow, g_row: GstRow,
                       base_status: str = "Matched"):
    """Append a paired match result with computed diffs."""
    inv_diff, tax_diff, igst_diff, cgst_diff, sgst_diff = compute_diffs(t_row, g_row)
    status = get_mismatch_status(inv_diff, tax_diff, igst_diff, cgst_diff, sgst_diff)
    if status == "Matched":
        status = base_status

    results.append(MatchResult(
        status=status,
        tally_row=t_row,
        gst_row=g_row,
        invoice_value_diff=inv_diff,
        taxable_value_diff=tax_diff,
        igst_diff=igst_diff,
        cgst_diff=cgst_diff,
        sgst_diff=sgst_diff
    ))


def match_rows(tally_rows: list[TallyRow], gst_rows: list[GstRow]) -> list[MatchResult]:
    results = []
    matched_tally = set()
    matched_gst = set()

    # Index GSTR-2B rows by GSTIN
    gst_by_gstin = {}
    for g in gst_rows:
        gst_by_gstin.setdefault(g.gstin, []).append(g)

    # Index rows by exact composite key (GSTIN + Invoice No + Party Name)
    gst_key_map = {}
    for g in gst_rows:
        key = make_key(g.gstin, g.invoice_no, g.trade_name)
        gst_key_map.setdefault(key, []).append(g)

    # ---------- Tier 1 (PRIMARY): GSTIN + Amount ----------
    # Same GSTIN and taxable value within Rs.10 -> matched
    for t in tally_rows:
        if t.row_index in matched_tally:
            continue

        candidates = [g for g in gst_by_gstin.get(t.gstin, [])
                      if g.row_index not in matched_gst]
        if not candidates:
            continue

        best = None
        best_diff = None
        for g in candidates:
            diff = abs(t.taxable_value - g.taxable_value)
            if diff <= THRESHOLD and (best is None or diff < best_diff):
                best = g
                best_diff = diff

        if best is not None:
            exact_key = make_key(t.gstin, t.voucher_ref_no, t.particulars) == make_key(
                best.gstin, best.invoice_no, best.trade_name
            )
            append_pair_result(
                results,
                t,
                best,
                base_status="Matched" if exact_key else "Matched (Amount Verified)",
            )
            matched_tally.add(t.row_index)
            matched_gst.add(best.row_index)

    # ---------- Tier 2 (SECONDARY): Exact GSTIN + Invoice No + Party Name ----------
    for t in tally_rows:
        if t.row_index in matched_tally:
            continue

        key = make_key(t.gstin, t.voucher_ref_no, t.particulars)
        candidates = [g for g in gst_key_map.get(key, [])
                      if g.row_index not in matched_gst]
        if not candidates:
            continue

        best = min(candidates, key=lambda g: abs(t.taxable_value - g.taxable_value))
        append_pair_result(results, t, best)
        matched_tally.add(t.row_index)
        matched_gst.add(best.row_index)

    # ---------- Tier 3a: Duplicates ----------
    matched_tally_keys = {
        make_key(t.gstin, t.voucher_ref_no, t.particulars)
        for t in tally_rows if t.row_index in matched_tally
    }
    for t in tally_rows:
        if t.row_index in matched_tally:
            continue
        key = make_key(t.gstin, t.voucher_ref_no, t.particulars)
        if key in matched_tally_keys:
            results.append(MatchResult(
                status="Duplicate in Tally",
                tally_row=t,
                gst_row=None
            ))
            matched_tally.add(t.row_index)

    matched_gst_keys = {
        make_key(g.gstin, g.invoice_no, g.trade_name)
        for g in gst_rows if g.row_index in matched_gst
    }
    for g in gst_rows:
        if g.row_index in matched_gst:
            continue
        key = make_key(g.gstin, g.invoice_no, g.trade_name)
        if key in matched_gst_keys:
            results.append(MatchResult(
                status="Duplicate in GSTR-2B",
                tally_row=None,
                gst_row=g
            ))
            matched_gst.add(g.row_index)

    # ---------- Tier 3b: Fallback labels ----------
    all_gst_gstins = set(gst_by_gstin.keys())
    all_tally_gstins = {t.gstin for t in tally_rows}

    for t in tally_rows:
        if t.row_index in matched_tally:
            continue
        if t.gstin in all_gst_gstins:
            status = "Invoice Value Mismatch; Taxable Value Mismatch"
        else:
            status = "In Tally but not in GSTR-2B"
        results.append(MatchResult(
            status=status,
            tally_row=t,
            gst_row=None
        ))

    for g in gst_rows:
        if g.row_index in matched_gst:
            continue
        if g.gstin in all_tally_gstins:
            status = "Invoice Value Mismatch; Taxable Value Mismatch"
        else:
            status = "In GSTR-2B but not in Tally"
        results.append(MatchResult(
            status=status,
            tally_row=None,
            gst_row=g
        ))

    return results


def get_summary(results: list[MatchResult]) -> dict:
    summary = {status: 0 for status in ALL_STATUSES}

    for r in results:
        if r.status in summary:
            summary[r.status] += 1
        else:
            for cat in VALUE_MISMATCH_CATEGORIES:
                if cat in r.status:
                    summary[cat] += 1

    return summary
from gst_reconciler.matcher import (
    ALL_STATUSES,
    MATCHED_STATUSES,
    MISMATCH_CATEGORIES,
    MatchResult,
    get_summary,
    match_rows,
)


def test_exact_match(make_tally, make_gst):
    results = match_rows([make_tally()], [make_gst()])

    assert len(results) == 1
    assert results[0].status == "Matched"
    assert results[0].tally_row is not None
    assert results[0].gst_row is not None


def test_same_gstin_with_similar_amounts_matches(make_tally, make_gst):
    tally = make_tally(invoice_no="TALLY001", party="TALLY PARTY")
    gst = make_gst(invoice_no="GST001", party="GST PARTY", taxable_value=1005.0)

    results = match_rows([tally], [gst])

    assert len(results) == 1
    assert results[0].status == "Matched (Amount Verified)"
    assert results[0].gst_row.row_index == gst.row_index


def test_nine_rupee_difference_is_matched(make_tally, make_gst):
    results = match_rows(
        [make_tally(taxable_value=1000.0)],
        [make_gst(taxable_value=1009.0)],
    )

    assert results[0].status == "Matched"


def test_ten_rupee_difference_is_matched(make_tally, make_gst):
    results = match_rows(
        [make_tally(taxable_value=1000.0)],
        [make_gst(taxable_value=1010.0)],
    )

    assert results[0].status == "Matched"


def test_eleven_rupee_difference_is_taxable_mismatch(make_tally, make_gst):
    results = match_rows(
        [make_tally(taxable_value=1000.0)],
        [make_gst(taxable_value=1011.0)],
    )

    assert results[0].status == "Taxable Value Mismatch"


def test_exact_three_key_match_pairs_rows_with_value_mismatch(make_tally, make_gst):
    tally = make_tally(taxable_value=1000.0)
    gst = make_gst(taxable_value=1200.0)

    results = match_rows([tally], [gst])

    assert len(results) == 1
    assert results[0].tally_row.row_index == 0
    assert results[0].gst_row.row_index == 0
    assert results[0].status == "Taxable Value Mismatch"


def test_duplicate_in_tally(make_tally, make_gst):
    first = make_tally(row_index=0)
    duplicate = make_tally(row_index=1)
    gst = make_gst(row_index=0)

    results = match_rows([first, duplicate], [gst])
    statuses = {result.status for result in results}

    assert statuses == {"Matched", "Duplicate in Tally"}
    assert len(results) == 2


def test_duplicate_in_gstr2b(make_tally, make_gst):
    tally = make_tally(row_index=0)
    first = make_gst(row_index=0)
    duplicate = make_gst(row_index=1)

    results = match_rows([tally], [first, duplicate])
    statuses = {result.status for result in results}

    assert statuses == {"Matched", "Duplicate in GSTR-2B"}
    assert len(results) == 2


def test_summary_has_nine_mismatch_categories():
    assert len(MISMATCH_CATEGORIES) == 9

    results = [
        MatchResult(status=status, tally_row=None, gst_row=None)
        for status in ALL_STATUSES
    ]
    summary = get_summary(results)

    assert set(summary) == set(ALL_STATUSES)
    assert set(summary) == set(MATCHED_STATUSES + MISMATCH_CATEGORIES)
    assert all(count == 1 for count in summary.values())


def test_summary_counts_combined_mismatch_statuses():
    results = [
        MatchResult(
            status="Invoice Value Mismatch; Central Tax Mismatch",
            tally_row=None,
            gst_row=None,
        )
    ]

    summary = get_summary(results)

    assert summary["Invoice Value Mismatch"] == 1
    assert summary["Central Tax Mismatch"] == 1

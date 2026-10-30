# Synthetic sample data

These files are **fictional** and contain no real taxpayer data. They are deterministic so the reconciliation output can be reproduced and verified.

| File | Purpose |
|---|---|
| `tally-purchases-apr-2025.xlsx` | Tally purchase register with 11 rows |
| `gstr2b-apr-2025.xlsx` | GSTR-2B workbook with 11 B2B rows |
| `reconciliation-report.xlsx` | Generated report; original GSTR-2B sheets are preserved |
| `expected_summary.json` | Expected counts and input row totals |
| `reconciliation-report.png` | Screenshot of the report sheet used in the README |

## Expected result

The sample produces **13 result rows**:

- 3 `Matched`
- 1 `Matched (Amount Verified)`
- 1 row for each of the 9 mismatch categories

The complete expected counts are in [`expected_summary.json`](expected_summary.json).

## Coverage

| Scenario | Tally invoice | GSTR-2B invoice | Expected status |
|---|---|---|---|
| Exact match | `INV-1001` | `INV-1001` | `Matched` |
| Amount verified | `TO-2001` | `GST-9001` | `Matched (Amount Verified)` |
| Tally only | `TO-3001` | — | `In Tally but not in GSTR-2B` |
| GSTR-2B only | — | `GST-4001` | `In GSTR-2B but not in Tally` |
| Invoice value | `INV-5001` | `INV-5001` | `Invoice Value Mismatch` |
| Taxable value | `INV-6001` | `INV-6001` | `Taxable Value Mismatch` |
| Integrated tax | `INV-7001` | `INV-7001` | `Integrated Tax Mismatch` |
| Central tax | `INV-8001` | `INV-8001` | `Central Tax Mismatch` |
| State/UT tax | `INV-9001` | `INV-9001` | `State/UT Tax Mismatch` |
| Duplicate in Tally | `INV-10001` ×2 | `INV-10001` | `Duplicate in Tally` |
| Duplicate in GSTR-2B | `INV-11001` | `INV-11001` ×2 | `Duplicate in GSTR-2B` |

## Reproducing the report

Launch the app and upload the two input files, then use **Download Report**. The generated workbook should match `reconciliation-report.xlsx` and the summary should match `expected_summary.json`.

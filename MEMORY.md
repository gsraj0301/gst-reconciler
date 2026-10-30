# Memory — GST Reconciler

## Project Overview

Desktop app that reconciles a Tally Voucher Register against GSTR-2B data, flags value/tax mismatches and duplicates, and writes a colour-coded report into a copy of the GSTR-2B workbook. No login, no required `.env`, no network calls.

## Tech Stack

- **Language:** Python 3.10+
- **GUI:** Tkinter + TkinterDnD2 (`tkinterdnd2`)
- **Data:** pandas + openpyxl
- **Packaging:** PyInstaller (`GST-Reconciler.spec`)
- **Testing:** pytest
- **CI/CD:** GitHub Actions (tests on push, Windows EXE on `v*` tags)

## Final State

- Branch: `main`
- Latest commit: `c38ddd1 docs: mark release phases complete`
- Release tag: `v1.0.0`
- Release: https://github.com/gsraj0301/gst-reconciler/releases/tag/v1.0.0
- Asset: https://github.com/gsraj0301/gst-reconciler/releases/download/v1.0.0/GST-Reconciler.exe
- EXE size: 35,417,374 bytes
- EXE SHA-256: `4fc603f219bdff7e04efc75680e0b40f4a62eb60c310d502212413dcfc358647`
- Test suite: 16 tests passing locally; CI matrix passes on Python 3.10/3.11/3.12

## Matching Semantics

- Tier 1: same GSTIN + taxable value within ₹10.
  - Returns `Matched` only when invoice number and party name also match.
  - Returns `Matched (Amount Verified)` when the 3-key match is absent.
  - Tax-head differences are still flagged.
- Tier 2: exact `GSTIN + Invoice No + Party Name`.
- Tier 3 fallbacks: duplicates, Tally-only/GSTR-only, and value-only mismatches.
- `Matched` and `Matched (Amount Verified)` are separate from the nine mismatch categories.
- Matching uses `MATCHED_STATUSES`, `VALUE_MISMATCH_CATEGORIES`, `MISMATCH_CATEGORIES`, and `ALL_STATUSES` in `gst_reconciler/matcher.py`.

## Commands

```bash
# Tests
python -m pytest

# App from source
python run.py

# Verify the sample report and expected summary
python -m pytest tests/test_sample.py

# Build EXE
pyinstaller GST-Reconciler.spec --clean
```

## CI and Release

- `.github/workflows/test.yml` runs pytest on every push.
- `.github/workflows/release.yml` runs on `v*` tags and attaches `dist/GST-Reconciler.exe` to the release.
- `v1.0.0` release run `41012793719` succeeded.
- Latest docs-only tests run `41015437362` succeeded.

## Key Files

- `run.py` — launcher
- `gst_reconciler/main.py` — TkinterDnD2 UI and upload flow
- `gst_reconciler/parser.py` — Tally/GSTR-2B parsing
- `gst_reconciler/matcher.py` — matching and summary
- `gst_reconciler/writer.py` — report generation with sheet preservation
- `gst_reconciler/__init__.py` — lazy `main` import so tests do not require TkinterDnD
- `tests/` — matcher, parser, writer, sample integration tests
- `sample/` — deterministic synthetic inputs, report, screenshot, expected summary
- `README.md` — usage, formats, matching logic, release link
- `PHASE.md` — completed delivery checklist

## Demo Data

- `sample/tally-purchases-apr-2025.xlsx`: 11 rows
- `sample/gstr2b-apr-2025.xlsx`: 11 rows
- `sample/reconciliation-report.xlsx`: 13 result rows
- Expected: 3 `Matched`, 1 `Matched (Amount Verified)`, and one row for each of the nine mismatch categories.
- `sample/reconciliation-report.png`: synthetic screenshot used in README.

## Caveats

- The Windows EXE was built and validated as PE32+ on GitHub's `windows-latest` runner but was not launched on Windows in this environment.
- The GUI flow was smoke-tested locally; full drag-and-drop interaction on Windows should still be verified on a real desktop.
- `Gst_portal_automation/gst_automation.py` contains a hardcoded secret and was intentionally never copied into this repo.

## Future Ideas

- Add a machine-readable JSON export of the reconciliation summary.
- Add a CLI entry point for scripted reconciliation.
- Add Windows code-signing to reduce SmartScreen warnings.

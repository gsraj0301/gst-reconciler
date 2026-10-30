# GST Reconciler — Delivery Plan

## Decisions

- The desktop app has **no password gate** and does **not** use a `.env` file.
- Launching the app goes directly to the upload screen.
- The README uses the real clone URL and the resume's **9 mismatch categories**.
- Demo data and screenshots must use synthetic, anonymized data only.
- Releases are published from tags and include build artifacts.

## Phase 1 — Remove authentication and fix documentation

- [x] Delete the login screen and all password handling from the app.
- [x] Remove `.env.example` and all `.env` / environment-variable instructions.
- [x] Launch directly into the upload screen.
- [x] Replace the placeholder clone URL with `https://github.com/gsraj0301/gst-reconciler.git`.
- [x] Replace the malformed badge table with valid badges.
- [x] Rename “Seven mismatch categories” to **“Nine mismatch categories”**.
- [x] Separate `Matched` / `Matched (Amount Verified)` from the 9 mismatch categories.
- [x] Remove all password/login references from the README.
- [x] Add the real GitHub hyperlink to the resume and regenerate the PDF.

## Phase 2 — Tests and CI

- [x] Add `requirements-dev.txt` with `pytest`.
- [x] Add `tests/` with 8–10 matching-logic tests:
  - exact 3-key match
  - ₹9 difference → matched
  - ₹11 difference → mismatch
  - exactly ₹10 → matched
  - duplicate in Tally
  - duplicate in GSTR-2B
  - same GSTIN with similar amounts
  - missing GSTIN
  - different column names / sheet names
  - 9 mismatch categories in the summary
- [x] Add parser tests for Tally aliases and GSTR-2B merged headers.
- [x] Add a writer smoke test for sheet preservation and report placement.
- [x] Add `.github/workflows/test.yml` running pytest on every push.
- [x] Add a passing tests badge to the README.

## Phase 3 — Demo data and screenshot

- [x] Replace the current sample files with deterministic synthetic data covering every status.
- [x] Add `sample/README.md` and `sample/expected_summary.json`.
- [x] Generate the reconciliation report from the sample files.
- [x] Add an anonymized report screenshot at `sample/reconciliation-report.png`.
- [x] Embed the screenshot in the README.

## Phase 4 — Releases

### GST Reconciler

- [x] Add `GST-Reconciler.spec`.
- [x] Add a Windows release workflow triggered by `v*` tags.
- [x] Build `GST-Reconciler.exe`.
- [x] Tag `v1.0.0` and write 3–4 lines of release notes.
- [x] Attach the executable and link the release from the README.

### GPexp

- [ ] Build or download the APK from GitHub Actions.
- [ ] Tag `v1.0.0` and write 3–4 lines of release notes.
- [ ] Attach the APK and link the release from the README.

## Phase 5 — Verification

- [x] Run `pytest -q`.
- [x] Launch the GUI and confirm it opens directly to upload.
- [x] Run the sample reconciliation and verify the expected summary.
- [x] Verify the screenshot contains no real data.
- [ ] Verify both releases and their assets.
- [ ] Run `git diff --check` and commit the changes.

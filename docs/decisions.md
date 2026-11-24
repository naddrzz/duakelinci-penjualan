# Decision log

Newest first. Each entry summarizes what was decided, why, and when to revisit it.

## 2026-11-24 — One-paragraph Telegram summary with regional breadth & per-outlet drop salesman

- **Single paragraph matching the brief (`"\n" not in text`)**: four concise sentences cover current-month net sales + month-over-month change, regional breadth (`Jawa Timur naik 92%, tetapi empat dari enam wilayah turun, terdalam Jawa Barat (14%)`), the 5 steepest `%` drop outlets with the salesman driving each drop, and the largest Rupiah losses on big wholesaler accounts.
- **Restrained formatting**: uses `**bold**` only on the headline figure and the two action leads (`**Lima outlet turun terdalam:**`, `**Rupiah terbesar hilang**`), `` `OUTxxxx` `` tap-to-copy outlet codes, and natural prose currency (`Rp878,4 juta`, `Rp31,6 juta`), rendered cleanly on `/` via `tg_preview_html()`.

## 2026-11-23 — Compact single-line tables & slide-over outlet detail panel on `/outlet-terlemah`

- **Single-line table rows**: stacking outlet IDs, store types, invoice counts, and salesman notes inside table cells pushed minimum table widths past `1 080px` and caused horizontal scrolling on `1366px` laptops. Keeping table rows single-line lets every table fit comfortably on laptop screens.
- **Slide-over detail panel (`#outlet-side-peek` via `Aksi` → `Detail`)**: clicking `Detail` opens a right-hand panel without blocking the table on the left, showing invoice frequency, carton volume, last order date, SKU-level status (`Semua / Berhenti / Jalan`), per-salesman sales changes, and the `Q1` calculation for that store, with `↑`/`↓` buttons and `Escape` to close.

## 2026-11-23 — Clean layout, tabbed 4-dimension breakdown & full salesman attribution

- **4-dimension breakdown (`/wilayah-merek?lihat=wilayah|cabang|merek|salesman`)**: added city branch (`13` branches) and salesman (`26` named salesmen + `Belum tercatat` for the `5` blank rows so totals still add up to `100%`) alongside region and brand, using horizontal tabs instead of a hidden dropdown.
- **Salesman attribution on declining outlets**: outlets are often served by two salesmen on different routes. Showing each salesman's `Sep → Okt` change inside the outlet detail panel (for example, at `OUT1043` Palembang `Zaki` dropped `−Rp 6,8 jt` while `Yudi` grew) tells a manager immediately who to follow up with.

## 2026-11-23 — Weakest-outlet rule: `%` drop with a 25th-percentile (`Q1`) minimum + Rupiah drop tab

- **Why a `Q1` minimum (`Rp 4.927.700` on the sample CSV)**: new stores (`base <= 0`) have no September baseline, and tiny warungs in the bottom 25% of September sales can show a `-70%` drop just from skipping one small order. Setting the cutoff at the 25th percentile (`Q1`, `adaptive_base_floor()`) filters out those small-denominator swings automatically and scales naturally when a user uploads a different CSV.
- **Why pair `%` drop with a Rupiah drop tab (`Kehilangan Rp`)**: `%` drop catches mid-size stores losing half their order volume, while sorting by rupiah loss catches large wholesalers (`Grosir Sentosa −Rp 31,6 jt`, `Grosir Sumber Alam −Rp 24,3 jt`) that drive most of the total lost revenue. Showing both tabs on `/outlet-terlemah` avoids hiding either problem.

## 2026-11-23 — In-memory custom CSV upload with stdlib multipart parsing

- **Zero extra dependencies**: `POST /api/upload` enforces a `10 MiB` cap (`MAX_UPLOAD_BYTES`) and parses `multipart/form-data` with Python's stdlib `email.parser.BytesParser` before running `load_sales_text()` and `build_report()` in memory. No `python-multipart` dependency or writable disk directory is needed.
- **Safe reset**: the startup report stays in `app.state.default_report`, so invalid uploads leave the active report untouched and `POST /api/report/reset` restores the sample data immediately. Revisit if multi-user session isolation or database persistence is needed.

## 2026-11-23 — Self-hosted assets, light theme, and progressive enhancement

- **Offline-ready**: `InterVariable.woff2`, `MontserratVariable.woff2` (both SIL OFL), logos, and favicons live in `app/static/` — zero external CDN or font requests.
- **Light theme & WCAG AA**: `color-scheme: light` with `>= 4.5:1` text contrast, `>= 3:1` controls/bars, visible focus rings, `44×44px` coarse-pointer touch targets, and zero horizontal page overflow down to `320px` width.
- **Server-rendered HTML first**: all three routes render complete HTML on the server; `app.js` progressively adds sorting, live filtering, tab switching, the detail panel, and smooth page transitions.

## 2026-11-23 — Python stdlib `csv`, startup precomputation, and duplicate/return rules

- **Stdlib `csv` + `collections` instead of pandas**: ~1,900 rows need only grouping and sums, keeping install time fast and dependencies minimal (`fastapi`, `uvicorn`, `jinja2`). Revisit if input grows to hundreds of thousands of rows.
- **Compute once at startup**: the CSV is static until a new file is uploaded, so building the report once in FastAPI's lifespan avoids redundant per-request work.
- **Drop exact duplicate rows, keep returns**: three byte-identical duplicate lines (`INV500201`, `INV500386`, `INV500791`) are double entries and dropped; `RTR900001` (`−2` cartons, `−Rp 528.000`) is a genuine product return and kept in net sales. See [data.md](data.md).

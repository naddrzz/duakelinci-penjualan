# Changelog

## 2.0.0 — 2026-11-23

- **Quiet architectural UI redesign & structured Tabbed Data Table** (approved from Wonder draft in workspace `insan-khamil` + follow-up table refinement):
  - Replaced boxed KPI cards, the multicolored stacked composition bar, and duplicate Ringkasan leaderboards with open **Stat Strips** (`dl.stat-strip` on `/` and `/outlet-terlemah`), generous `44px` vertical rhythm on a pure-white canvas (`#FFFFFF`) beside a warm-stone sidebar (`#FAFAFA`), and a clean document-sheet treatment for the Telegram briefing.
  - Renamed the `/wilayah-merek` navigation item to **Rincian penjualan** (covering all 4 dimensions) and converted the page into a focused **Tabbed Data Table** (`div.tabbed-sheet` + `Wilayah 6`, `Cabang Kota 13`, `Merek 8`, `Salesman 26` tabs) with auto-numbered `#` rows, `Selisih` & `Total` full-rupiah columns, inline share bars, and a `Total Keseluruhan` footer.
  - Added an **Aksi → `Detail`** column and **Notion-style Right Side Peek** (`#outlet-side-peek`) on `/outlet-terlemah` (researched on Mobbin & approved in Wonder): non-blocking right drawer with active-row highlight, `»` close (`Escape`), `↑`/`↓` row stepping, one-click `Salin detail`, enriched Notion properties (branch, region, salesmen, invoice frequency & drop size, carton volume, SKU count, last order date/salesman, brands), interactive **Status & Pergerakan SKU** (`Semua / Berhenti / Jalan` per SKU with carton movement & salesman), per-salesman drop attribution cards, and exact Q1 calculation ledger.
  - Styled all data tables across `/`, `/wilayah-merek`, and `/outlet-terlemah` as **clean structured tables** (`1px` rounded border frame, `#FAFAFA` sticky header & footer, subtle column hairlines, `tabular-nums` alignment, no horizontal thin scrollbar, and compact single-line cells so all columns fit cleanly on laptop viewports).
  - **Mobile-native polish & horizontal table sync**: synchronized `thead` and `tbody`/`tfoot` horizontal scrolling on `.numbered-table` and narrow viewports (`<= 720px`), converted `/wilayah-merek` dimension tabs into a single-row edge-to-edge swipeable strip, upgraded `/` Stat Strip and outlet filters to balanced `2×2` phone grids (`1-col` below `360px`), refined `#outlet-side-peek` mobile property/SKU/ledger rows and `44×44px` non-overlapping touch targets, converted `#upload-dialog` into a bottom sheet on phones, and added `viewport-fit=cover`, `interactive-widget=resizes-content`, `theme-color`, `enterkeyhint="search"`, safe-area insets, and coarse-pointer autofocus gating.
  - **Hardened offline Docker bundle (`Dockerfile`, `.dockerignore`, `compose.yaml`, `app/main.py`)**: explicit `mimetypes` registration (`font/woff2`, `image/x-icon`, `image/png`, `text/css`, `text/javascript`) for minimal `slim` images, whitelist `.dockerignore`, `chmod -R a+rX /app` + build-time verification of every font (`InterVariable.woff2`, `MontserratVariable.woff2`, OFL licences), logo, favicon, template, and CSV as `appuser`, configurable `PORT`, and a `read_only: true` `compose.yaml`.

## 1.9.0 — 2026-11-23

- **Chat-First Telegram briefing (`telegram_summary()` & `ringkasan.html`)**:
  - Redesigned around Sales Manager daily mobile workflow (concise macro positives up top, deep operational diagnostics on declines) and elevated the Telegram card to the primary fold on `/`.
  - Added best **Region (branch group area)** with its **Branch (city)** breakdown (`Jabodetabek`: `Tangerang`, `Jakarta Barat`, `Bekasi`) plus top city branch overall, best **Brand**, top **Salesman** (`Citra`), **Highest vs Lowest Sales** with `[outlet_id]` and salesman (`[OUT1007]` vs `[OUT1003]`, lowest region/branch/brand/salesman), and per-outlet **Salesman + drop-driver attribution** on all declining retail and key wholesaler accounts.
- **Salesman & Branch visibility across all three pages**:
  - `/` (`ringkasan.html`): added Region + Branch breakdown in the top KPI, Salesman KPI & 4-pillar leaderboards (`Wilayah`, `Cabang`, `Merek`, `Salesman`), Highest/Lowest extremes card, and a `Salesman` column + `#f-branch` & `#f-salesman` filters in `#outlet-table`.
  - `/wilayah-merek` (`wilayah_merek.html`): added `Per cabang (13 cabang)` and `Per salesman (26 salesman)` views alongside `Per wilayah` and `Per merek`, plus cross-dimensional branch and top-salesman columns in every table.
  - `/outlet-terlemah` (`outlet_terlemah.html`): added `Salesman & sumber drop` column to both `%` erosion and `Rp` *Revenue-at-Risk* tables (pinpointing which salesman's orders contracted at shared outlets), an interactive search bar (`#weak-search`), and `[outlet_id]` + salesman labels across funnel and comparison lists.
  - Universal multi-token table search (`matchesQuery` in `app.js`): every data table across `/`, `/wilayah-merek` (all 4 views), and `/outlet-terlemah` now includes a live search bar supporting store name, outlet ID (`OUT10xx`), salesman name, city branch, region, store type, brand, and status.

## 1.8.3 — 2026-11-23

- Added self-hosted web favicons derived proportionally from `logo-dk.png` without aspect-ratio distortion (`favicon.ico` at `16×16`/`32×32`/`48×48`, `favicon.png` at `64×64`, and `apple-touch-icon.png` at `180×180`), wired into `base.html` and `GET /favicon.ico`.

## 1.8.2 — 2026-11-23

- Hardened mathematical edge cases in `app/analysis.py` and templates:
  - `adaptive_base_floor()` now uses `math.ceil(q1)` instead of `round(q1)` so integer rupiah comparisons (`base >= floor`) remain strictly equivalent to `base >= Q1` even when linear quartile interpolation yields `.25`/`.5`/`.75` fractional rupiah.
  - Enforced strict disjoint funnel partitioning (`base <= 0` vs `0 < base < min_base_idr` vs `base > 0 and base >= min_base_idr`) so tiny custom CSVs (`< 4` active outlets, `floor = 0`) never double-count new outlets.
  - Excluded negative return credit notes (`qty_carton <= 0`) from per-outlet sales-order invoice counts (`base_invoices`, `current_invoices`) and clamped CSS bar widths to `[0%, 100%]`.

## 1.8.1 — 2026-11-23

- Removed intermediate rounding from `adaptive_base_floor()`: the weakest-outlet materiality threshold now uses the **exact unrounded 1st quartile (`Q1 = Rp 4.927.700` on the 51 active sample outlets; `12` outlets `< Q1` excluded, `39` eligible)** so boundary outlets are never misclassified, and added the explicit `Q1` formula row to `/outlet-terlemah`.

## 1.8.0 — 2026-11-23

- **Dual-Lens FMCG weakest-outlet model & adaptive Q1 floor** (`app/analysis.py`, `outlet_terlemah.html`):
  - Replaced the static base-sales cutoff with a data-driven 1st-quartile (`Q1 / P25`) materiality floor (`adaptive_base_floor()`, resolving to `Rp 5.000.000` from `Q1 = Rp 4.927.700` on the sample CSV and adapting automatically on custom CSV uploads).
  - Added a segmented **Kemerosotan %** vs **Kehilangan Rp** (*Revenue-at-Risk*) switcher at the top of `/outlet-terlemah`, per-outlet invoice & SKU movement (`Sep→Okt`), and an **Empirical Bayes Shrinkage** cross-validation card.
- **Telegram summary**: includes both the numbered top-5 `%` erosion outlets and a concise callout for top key-account rupiah drops (`Grosir Sentosa`, `Grosir Sumber Alam`) when distinct from the `%` list.

## 1.7.0 — 2026-11-23

- Added **Unggah CSV** feature (`POST /api/upload`, `POST /api/report/reset`, `GET /api/sample-csv`) so users can upload any UTF-8 CSV following the 15-column sample schema (comma or semicolon delimited, up to 10 MB) directly from the sidebar, mobile bar, or data notes footer.
- Accessible `<dialog>` modal with drag-and-drop / file picker, inline Bahasa Indonesia validation errors (missing columns, invalid row types, `< 2` months, or `.xlsx` uploads), sample CSV template download link, active custom-data badge, and one-click reset back to the bundled sample dataset.

## 1.6.1 — 2026-11-23

- Wilayah & merek (`/wilayah-merek`): moved `form.view-switch` from the page header into the "Tabel penjualan per wilayah/merek" card header and kept both view selects synchronized without vertical jump on switch.

## 1.6.0 — 2026-11-23

- Replaced the horizontal top navbar with a collapsible vertical sidebar (`#sidebar`) featuring hide/unhide controls (`[data-sidebar-toggle]` and `Ctrl+B`/`Cmd+B`), flash-free `localStorage` state persistence on desktop, and a dismissible off-canvas drawer with backdrop + `Escape` support on mobile/tablet (`<= 960px`).

## 1.5.4 — 2026-11-23

- Outlet terlemah (`/outlet-terlemah`): converted "Hasil dan hitungannya" from multi-card blocks into a sortable full-rupiah table (`#weakest-table`) with inline calculation formulas and remaining-share bars, and moved it to the top of the page above the methodology and 5-step filtering funnel.

## 1.5.3 — 2026-11-23

- Semantic & neutral bar colors across all three pages: `.bar` now defaults to neutral slate (`--bar-neutral`), while bars paired with growth/decline metrics (`m.bar(width_pct, change)`) render green (`--bar-pos`) for positive growth and red (`--bar-neg`) for declines so positive items never appear in red.
- Updated the 8-segment share composition bar on `/wilayah-merek` (`--seg-0..7`) to a non-alarm sRGB-clamped categorical palette starting with slate-blue instead of crimson.

## 1.5.2 — 2026-11-23

- Fixed `<select>` width shifting under `appearance: base-select` when switching between options in `form.view-switch` (`/wilayah-merek`) and the outlet filters/sort controls (`/`).

## 1.5.1 — 2026-11-23

- Clean UI pass: removed the corporate crimson footer blocks (`div.corp-inner` / `div.corp-band` and `div.corp-subband`), switched all KPI cards to pure white surfaces without green fills, removed colored top/side border strips across cards, unboxed the page header, and stripped repeated uppercase eyebrows for a quieter, restrained hierarchy.

## 1.5.0 — 2026-11-23

- Full frontend redesign aligned with `duakelinci.com/en`: official Dua Kelinci crimson (`#D61A21` family) and heritage leaf green (`#1BAB51` / `#0C8037` family) authored in sRGB-clamped OKLCH tokens with P3 enhancement, pill CTAs, `20px` concentric card surfaces with layered shadows, and a two-tier footer pairing CSV cleaning audit stats with the PT Dua Kelinci corporate band.
- Self-hosted `MontserratVariable.woff2` (SIL OFL) for display headings paired with `InterVariable.woff2` for body copy and `tabular-nums` figures, plus self-hosted Dua Kelinci logos (`logo-dk.png`, `logo-dk-white.png`) — zero external requests.
- Ringkasan (`/`): new executive hero banner, heritage-green featured total-sales card, top-4 region & brand contribution leaderboards, and a 5-outlet priority watch preview above the Telegram card, "Sekilas" movement card, and interactive all-outlets directory.
- Wilayah & merek (`/wilayah-merek`): dimension switcher integrated into the hero, accented summary tiles, and an 8-color stacked share composition bar above the full-rupiah table.
- Outlet terlemah (`/outlet-terlemah`): side-by-side rule/formula and 5-step funnel layout, redesigned diagnostic calculation cards with retention bars, and updated skeletons in `app.js`.

## 1.4.1 — 2026-11-23

- Status filter: the selected pill now slides to the new option.
- Dropdowns: styled picker (rounded, shadow, tinted highlight without a side bar, checkmark, open animation) in Chrome/Edge/Safari; native picker elsewhere.
- Focus: the thick black focus box is replaced by a thin orange ring, and by an orange border with a soft halo on fields and dropdowns.
- Outlet table toolbar tidied: search and filters in one flowing row of equal-height controls; outlet count, reset and "Urutkan" share a row below a divider; full-width controls on phones.

## 1.4.0 — 2026-11-23

- Split into three pages: Ringkasan (`/`), Wilayah & merek (`/wilayah-merek`), Outlet terlemah (`/outlet-terlemah`).
- Ringkasan: KPIs, Telegram text, "Sekilas" facts and the all-outlets table.
- Wilayah & merek: dropdown picks the region or brand table; wider table with full rupiah values, difference column and summary tiles.
- Outlet terlemah: rule and formula, step-by-step filtering (52 → 51 → 38 → 21 → 5), each outlet's calculation, comparison with "lowest total" and "largest rupiah drop".
- Page changes animate, with a progress bar and a page-shaped skeleton; reduced-motion respected.
- CSS and JS moved to `app/static/` with cache-busting URLs.

## 1.3.0 — 2026-11-23

- Dashboard layout: sticky top bar with section links, primary "Salin ringkasan Telegram" action in the header, KPI cards with delta pills, weakest outlets beside the Telegram card.
- New "Semua outlet" table with search, region/type filters, status filter (Perlu perhatian / Turun / Naik), sort select (A–Z, Z–A and more), live result count and empty state.
- Every table: lines between rows and columns, sortable column headers (`aria-sort`), sticky header and first column.
- Light theme only.

## 1.2.1 — 2026-11-23

- Inter is now self-hosted (`/static/fonts/InterVariable.woff2`, SIL OFL); the page makes no external requests and works offline.

## 1.2.0 — 2026-11-23

- Flat, modern look: neutral surfaces, 1px borders, no shadows, single orange accent; total-sales card as a solid accent block.
- Inter font (Google Fonts, system font fallback).

## 1.1.0 — 2026-11-23

- Redesigned page: warm report palette, serif headings, KPI cards for total / best region / best brand / outlets needing attention, section navigation.
- Weakest outlets shown as a mobile-friendly list with a "remaining share of September sales" bar.
- Accessibility: WCAG AA contrast in light and dark, skip link, keyboard-focusable table scroll regions with sticky first column and header, always-visible styled table scrollbars, 44px targets, reduced-motion, high-contrast and print support.

## 1.0.0 — 2026-11-23

- First release: one-page summary with sales per region and brand, 5 weakest outlets (largest % drop Sep→Okt, base ≥ Rp 5 jt), and a copy-ready Telegram paragraph.
- CSV cleaning: region aliases, whitespace trimming, duplicate removal, returns kept; data notes shown in the page footer.
- `GET /api/report` JSON and `GET /healthz`.
- Docker image (non-root, healthcheck).

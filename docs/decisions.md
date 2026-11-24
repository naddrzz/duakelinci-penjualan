# Decision log

Newest first. Each entry: what was decided, why, and what would make us revisit it.

## 2026-11-24 — Stacked Telegram formatting (`**bold**`, tap-to-copy `` `OUTxxxx` ``, EYD V `Rp` + `U+00A0`) & natural Indonesian microcopy (requested & paste-tested by the user)

- **Native client-side entities over flat plain text**: real paste testing in Telegram Desktop and Android showed that flat weight and >100-character lines created an exhausting wall of wrapped text with orphaned `Rp` and `jt` fragments. Using `**...**` (`messageEntityBold`) on section headers, store names, and key deltas plus `` `OUTxxxx` `` (`messageEntityCode`, enabling 1-tap clipboard copy in Telegram) provides clear visual hierarchy across Desktop, Android, and iOS while keeping `<div class="tg-doc" data-tg-preview>` rendered cleanly without raw asterisks on the web dashboard.
- **EYD V currency spelling + `U+00A0` non-breaking unit glue (`rp_tg`)**: attaching `Rp` directly to digits (`Rp847,5\u00A0jt`, `−Rp6,3\u00A0jt`) per EYD Edisi V Bab II.F.5 & II.G.3 and binding compact units (`rb`, `jt`, `miliar`, `faktur`) with `U+00A0` eliminates orphaned currency prefixes and unit suffixes on narrow mobile chat bubbles.
- **Stacked 1-facet-per-line cards & lugas Bahasa Indonesia**: each bullet/numbered item places store + ID + city, rupiah/percent movement, invoice cadence, and salesman attribution on dedicated short lines separated by blank lines, replacing stiff nominal translations (*"Salesman kontraksi terdalam"*, *"drop utama"*, *"Perbandingan:"*, repeated *"dari total"*) with concise everyday commercial Indonesian (*"Sales turun terdalam"*, *"Zaki turun Rp6,8 jt"*). Full citations in [research-telegram-formatting-and-bahasa-indonesia.md](research-telegram-formatting-and-bahasa-indonesia.md).

## 2026-11-23 — Single-line structured tables & Notion-style Right Side Peek on `/outlet-terlemah` (researched via Mobbin, drafted in Wonder & approved by the user)

- **Keeping tables scannable without losing deep field diagnostics**: cramming outlet codes, store types, invoice/SKU cadence (`5→3 faktur · 9→5 SKU`), salesman drop notes, and division formulas underneath table cells pushed minimum table width past `~1 080px` and triggered horizontal scrollbars on `1280px–1366px` laptops. Stripping secondary cell sub-lines keeps every table across `/`, `/wilayah-merek` (**Rincian penjualan**), and `/outlet-terlemah` single-line and 100% fit on laptop viewports without horizontal thin scrollbars.
- **Notion-style non-blocking Side Peek (`#outlet-side-peek` via `Aksi` → `Detail`)**: modeled after Notion's web Side Peek flow on Mobbin, clicking `Detail` slides in a `492px` right panel separated by a `1px` border and leftward shadow **without a dark desktop backdrop scrim**, keeping the table on the left readable and interactive while highlighting the active row (`tr.is-peeked`). Includes `»` collapse (`Escape`), `↑`/`↓` row stepping (button & arrow keys), `Salin detail`, 2-column Notion properties (branch, region, salesmen, invoice frequency, SKU breadth, ordered brands), per-salesman contribution cards, and the exact Q1 validation ledger.

## 2026-11-23 — Quiet architectural redesign: open stat strips, underline dimension tabs & horizontal-hairline tables (designed in Wonder & approved by the user)

- **Eliminating card soup & color clutter**: replaced boxed 4-card KPI rows, the 27-segment multicolored share composition bar, and duplicate Ringkasan leaderboards with an open pure-white canvas (`#FFFFFF`) beside a warm-stone sidebar (`#FAFAFA`), generous section spacing (`gap: 44px`), and open **Architectural Stat Strips** (`dl.stat-strip`) separated only by `1px` vertical hairlines.
- **Underline Dimension Tabs (`[data-dim-nav]`)**: replaced the tucked-away `<select>` view switcher on `/wilayah-merek` with top-level underline tabs (`Wilayah 6`, `Cabang Kota 13`, `Merek 8`, `Salesman 26`) so all four dimensions are visible at a glance, progressively enhanced in `app.js` via `history.replaceState`.
- **Horizontal-hairline tables & monochrome proportion bars**: stripped vertical table gridlines and outer table-box borders so right-aligned `tabular-nums` figures carry the column structure cleanly, and replaced rainbow stacked bars with a single `4px` neutral bar per row (crimson accent reserved strictly for `#1` rank / final funnel step and primary CTA).

## 2026-11-23 — Chat-First Telegram pulse, asymmetric detail & full Region → Branch → Salesman → Outlet attribution (requested by the user)

- **Chat-first operating model (aligned with PT Dua Kelinci & ITB automation workflow)**: in day-to-day commercial operations, Head of Sales and Regional Managers read the **Telegram/Teams summary daily on mobile** and open the web dashboard only when drilling down into specific territories or coaching reps. Therefore `Ringkasan untuk Telegram` is elevated to the primary fold on `/` right beneath the KPI row, and every figure in the message connects directly to filterable views in the dashboard.
- **Asymmetric executive detail ("concise on upside, deep on decline")**:
  - *Upside & general standing*: managers only need clean macro orientation — best **Region** (branch group area, e.g. `Jabodetabek`) paired with its **Branch** breakdown (`Tangerang`, `Jakarta Barat`, `Bekasi`) and top city branch overall, best **Brand** (`Kacang Dua Kelinci`), top **Salesman** (`Citra`), and **Highest vs Lowest Sales** across outlets (`[OUT1007]` vs `[OUT1003]`), regions/branches, brands, and salesmen.
  - *Decline diagnostics*: when an outlet drops, managers need actionable field attribution immediately — **`[outlet_id]`** (crucial because store names like *Toko Sinar Abadi* repeat across outlets), **Branch & Region**, `Sep → Okt` rupiah & `%`, invoice cadence (`base -> current`), **assigned Salesmen**, and **which salesman actually drove the drop** (e.g., at `OUT1014 Grosir Sentosa` Bandung, `Gita` dropped `−Rp 37,6 jt` while `Hendra` grew `+Rp 5,9 jt`; at `OUT1043` Palembang, `Zaki` dropped `−Rp 6,8 jt` while `Yudi` grew).
- **4-dimension drill-down (`/wilayah-merek?lihat=wilayah|cabang|merek|salesman`) & salesman filters**: added city-branch and salesman breakdowns alongside region and brand, plus per-outlet salesman attribution and `#f-branch` / `#f-salesman` filters on `#outlet-table`. Unassigned CSV rows (`blank_salesman`) remain transparent in table totals (`Belum tercatat`) while `named_salesmen` drives top/bottom rep rankings so missing-name rows never distort human rankings.

## 2026-11-23 — Dual-Lens FMCG weakest-outlet evaluation, adaptive Q1 floor & structured Telegram summary (requested by the user)

- **Dual-Lens FMCG evaluation (`/outlet-terlemah` & `app/analysis.py`)**: pairs **Kemerosotan % terdalam** (comparable-store velocity erosion for churn risk) with **Kehilangan Rp terbesar** (*Revenue-at-Risk* for key wholesaler accounts, capturing `68,5%` of total lost rupiah vs `21,0%` on `%` alone) behind a segmented lens switcher at the top of `/outlet-terlemah`, enriched with per-outlet invoice & SKU movement (`base -> current`) and an **Empirical Bayes Shrinkage** cross-check.
- **Exact unrounded Q1 materiality floor (`adaptive_base_floor`)**: replaces static or rounded cutoffs with the exact 1st quartile (`P25`, position `0.25 × (N + 1)`) of active base-month outlets (`Q1 = Rp 4.927.700` on the sample CSV: `12` excluded, `39` eligible) grounded in De Moivre's equation ($\sigma_{\bar{x}} = \sigma/\sqrt{n}$). Avoiding intermediate rounding prevents boundary-shift misclassification while adapting automatically to custom CSVs of any currency scale.
- **Structured multi-line Telegram summary (`telegram_summary()`)**: 3–4 scannable blocks (period headline, bulleted KPIs, numbered `1.`–`5.` `%` erosion watch list with `%` + `−Rp`, plus non-duplicate top key-account rupiah drops) backed by NN/g mobile scanning studies, Smart Brevity / BLUF, and Telegram's `lineBreaks: .keep` paste behavior (full citations in [research-weakest-outlet-and-telegram.md](research-weakest-outlet-and-telegram.md)).

## 2026-11-23 — In-memory custom CSV upload with stdlib multipart parsing (requested by the user)

- **Zero extra dependencies**: `POST /api/upload` streams the request body with a strict `10 MiB` cap (`MAX_UPLOAD_BYTES`) and parses `multipart/form-data` via Python's stdlib `email.parser.BytesParser` before running `load_sales_text()` and `build_report()` in memory. This keeps `requirements.txt` free of `python-multipart` and works on read-only container filesystems.
- **Same validation & cleaning pipeline**: uploaded CSVs go through the exact 15-column schema, region alias normalization, deduplication, and `>= 2` month checks as the startup CSV, plus automatic `;` delimiter detection for Indonesian-locale Excel CSV exports and friendly Bahasa Indonesia error messages (including `.xlsx` detection).
- **Safe state & instant reset**: the startup report stays cached in `app.state.default_report`, so invalid uploads leave the current report untouched and `POST /api/report/reset` restores the sample dataset instantaneously. Revisit if uploaded datasets need per-user session isolation or persistent database storage in a multi-tenant deployment.

## 2026-11-23 — Clean, restrained Dua Kelinci redesign (requested by the user)

References studied: `https://duakelinci.com/en` (`#D61A21` corporate crimson, `Montserrat` display headings, pill primary CTA), Mobbin analytics screens (Shopify, Square, Causal, Churnkey, Monarch), and visual feedback requesting a cleaner surface without green KPI fills, colored card border strips, or the red corporate footer block.

- **Restrained OKLCH palette (`app/static/app.css`)**: crisp white cards (`--surface: oklch(1 0 0)`) over a subtle warm-alabaster canvas (`--bg: oklch(0.985 0.002 65)`), paired with charcoal ink and **one** brand accent (`--brand-red: oklch(0.515 0.198 26.5)`) reserved strictly for the primary CTA and active nav underline. Data bars default to neutral slate (`--bar-neutral: oklch(0.555 0.015 250)`) and switch to semantic green (`--bar-pos: oklch(0.545 0.132 152)`) or red (`--bar-neg: oklch(0.545 0.185 26.5)`) via `m.bar()` only when paired with a `+`/`−` movement metric (or declining outlet retention), preventing positive growth items from displaying misleading red bars. The 8-segment composition bar on Wilayah & merek uses a non-alarm categorical palette (`--seg-0..7`) starting from slate-blue instead of crimson. No card carries a colored top/side border strip or solid accent background.
- **Typography pairing (100% self-hosted)**: `MontserratVariable.woff2` (SIL OFL, weights 500–800) pairs with `InterVariable.woff2` (body copy, controls, `tabular-nums` data columns), plus `logo-dk.png` in `app/static/` — zero external network requests.
- **Clean layout & collapsible sidebar**: replaced the horizontal top navbar with a left vertical sidebar (`#sidebar`, `252px`) that can be hidden/unhidden (`[data-sidebar-toggle]` or `Ctrl+B`/`Cmd+B`), persisted in `localStorage` (`dk-sidebar`) via a pre-paint `<head>` check so refreshing never flashes, and rendered as an off-canvas drawer with backdrop + `Escape` on `<= 960px` (`<noscript>` keeps navigation visible without JS). Content uses an open page header directly on the canvas, subtle 2-layer hairline card elevation (`16px` outer → `10px` inner → `7px` nested; `999px` pill buttons), top-4 region/brand leaderboards and 5-outlet watch preview on Ringkasan, an 8-color stacked share bar on Wilayah & merek, a top-positioned sortable calculation table (`#weakest-table`) above the side-by-side rule and 5-step funnel on Outlet terlemah, and a minimal border-top `Catatan data` footer.
- **Mobile & accessibility**: verified zero horizontal page scroll down to `320px` width across all three routes, `16px` (`1rem`) minimum font size on all form controls to prevent iOS zoom, neutral dark focus outlines (`--focus`), ≥ 44px primary touch targets, capability-gated `:hover`, `forced-colors` fallbacks, and strict `prefers-reduced-motion` handling.

## 2026-11-23 — Softer focus style, sliding segmented control, styled dropdown picker (requested by the user)

- **Focus**: the user asked to remove the thick black focus boxes. Removing focus indicators would leave keyboard users lost (WCAG 2.4.7), so they were **restyled, not removed**: a 2px accent ring (`--focus`, 3.6:1 on white) on buttons, links and table regions; text fields and dropdowns show an accent border plus a soft halo (`--focus-halo`) instead of an outline. Do not set `outline: none` without one of these replacements.
- **Segmented control** (status filter on Ringkasan): one `.seg-indicator` slides under the checked option (240 ms, `cubic-bezier(0.2, 0, 0, 1)`, CSS transitions so rapid changes retarget). `app.js` measures the checked label (`offsetLeft/Top/Width/Height`), so it also works when the control wraps to two rows; it re-measures without animation on resize and after the font loads. Without JS, the checked label keeps its own background. Reduced motion: it jumps.
- **Dropdowns** use customizable `<select>` (`appearance: base-select`, Chrome/Edge 135+, Safari 27+) inside `@supports`: rounded picker with shadow, options highlighted on hover/keyboard with an orange tint and darker text (no side bar), a ✓ on the selected option, a rotating chevron and a 160 ms fade/slide when opening. Other browsers (Firefox) keep the native picker, so nothing breaks. The markup stays a plain `<select>`.

## 2026-11-23 — Three pages, animated page changes with skeletons (requested by the user)

- **Pages**: Ringkasan (`/`: KPIs, Telegram text, all-outlets table), Wilayah & merek (`/wilayah-merek`: one wide table at a time, picked with a dropdown so each table gets the full width and shows full rupiah values), Outlet terlemah (`/outlet-terlemah`: rule, formula, filtering steps with counts, per-outlet calculation, comparison with two other definitions). The region/brand choice lives in `?lihat=` so a view can be bookmarked and works without JavaScript (the form falls back to a submit button inside `<noscript>`).
- **Multi-page, enhanced by a small router** rather than a single-page app: every route is complete server-rendered HTML (works without JS, crawlable, no duplicated rendering). `app.js` intercepts in-app links to add a progress bar, an exit fade, a skeleton and an entrance animation. Revisit if pages start needing data the server cannot render.
- **Skeleton minimum 350 ms.** Pages render in a few milliseconds locally; a skeleton shown for 10 ms reads as a flicker, so once shown it stays 350 ms. Each route has its own skeleton shaped like its real layout so nothing jumps when content arrives.
- **Motion** (values from the `better-ui` skill): exit is an opacity fade of 120 ms; entrance is one-off keyframes of 300 ms with `cubic-bezier(0.2, 0, 0, 1)`, 12px rise and 4px blur, children staggered 60 ms; the region/brand switch replays a 240 ms entrance. Under `prefers-reduced-motion: reduce` only opacity changes, and the skeleton shimmer and progress bar animation stop.
- **Accessibility of page changes**: `<main aria-busy="true">` while loading; `document.title` updates; focus moves to the new `<h1>` (`tabindex="-1"`) or the URL hash target; the active nav item uses `aria-current="page"` plus an underline, not color alone.

## 2026-11-23 — Dashboard layout, interactive tables, light theme only (requested by the user)

References studied on Mobbin: Shopify Analytics and Apollo (KPI row, delta pills), Deel, Navattic and Origin (table toolbar: search left, filter chips, sort control, result count), Neon (full grid lines).

- **Light theme only.** `color-scheme: light`; no dark tokens. All tokens live in `:root` of `app/static/app.css`. Text pairs ≥ 4.5:1; control borders, bars and the scrollbar thumb ≥ 3:1. Table grid lines (`--line`) are decorative separators and exempt.
- **Layout** (DOM order = reading order): sticky top bar with section links → page header with the one primary action, "Salin ringkasan Telegram" → 4 KPI cards → region and brand tables (side by side only when each gets ≥ 660px, otherwise stacked) → weakest outlets next to the Telegram card → full-width "Semua outlet" table → data notes. Content max width 1440px.
- **Tables** draw lines between every row and column, have a sticky header and first column, and live in a keyboard-focusable `role="region"` scroll box with an always-visible scrollbar.
- **Sorting** on every table: each sortable header is a `<button>` inside a `<th>` whose `aria-sort` holds the state; the sorted column shows a single arrow. Text sorts with `Intl.Collator("id")` (A–Z / Z–A); numbers numerically; empty values (new outlets) always last. The outlet table also has an "Urutkan" select with explicit A–Z/Z–A options, kept in sync with the headers.
- **Search and filters** on the outlet table only (the region and brand tables have 6 and 8 rows): free-text search over name, ID, branch, region and type; region and outlet-type selects; a status segmented control (Semua / Perlu perhatian / Turun / Naik) with counts. The result count is a polite live region; no matches shows an empty state naming the query with a "Hapus semua filter" button.
- **Progressive enhancement**: the server renders the full, already sorted table; JavaScript only reorders and hides rows. The toolbar stays `hidden` until the script runs.

## 2026-11-23 — Flat palette and Inter (requested by the user)

Replaces the warm palette and serif headings below. The dark theme described here was later removed (see the entry above).

- **Flat**: solid fills and 1px borders; no shadows or gradients. Neutral grey surfaces with one orange accent (`--accent` for fills, `--accent-text` for text). The total-sales card is a solid accent block with white text. Every text pair is ≥ 4.5:1 and bars/scrollbar thumb ≥ 3:1 in light and dark.
- **Inter** for all text, **self-hosted**: `app/static/fonts/InterVariable.woff2` (official variable font from rsms.me, weights 100–900, 344 KB) with its SIL OFL 1.1 licence in `LICENSE-Inter.txt`. Served at `/static/fonts/`, preloaded, `font-display: swap`. The page makes no external requests, so it works offline. To update Inter, replace the woff2 file from https://rsms.me/inter/ and keep the licence file next to it.

## 2026-11-23 — UI redesign: accessibility first

- Palette and font were later replaced (see the entry above). Colour tokens live in `:root` at the top of `app/static/app.css`; re-check WCAG AA contrast whenever you change one.
- **KPI cards answer the three questions first** (total, best region/brand, outlets needing attention) before the detail tables.
- **Weakest outlets as a list, not a table**: it reflows on phones without sideways scrolling; each row shows how much of September's sales remain.
- **Scrollbars**: the page scrollbar stays native. Only the table scroll areas get a styled, always-visible 12px scrollbar so overflow is obvious; each one is a focusable `role="region"` for keyboard users, with a sticky first column and header.
- Also: skip link, 44px touch targets, neutral focus ring, hover effects only on real pointers, `prefers-reduced-motion`, Windows high-contrast (`forced-colors`) and print styles.

Revisit if Dua Kelinci provides official brand colors or fonts.

## 2026-11-23 — "Weakest outlet" = largest % decline with a Rp 5 jt base floor

The brief left "weakest" undefined. Lowest total flags small-but-growing outlets; largest rupiah drop flags big wholesalers that are still top outlets. % decline with a minimum base-month size flags outlets that are actually fading. Full reasoning in [metrics.md](metrics.md#2-weakest-outlets). Revisit if the sales team wants "revenue at risk" instead, in which case rank by `change_idr`.

## 2026-11-23 — Python stdlib `csv` instead of pandas

~1,900 rows; grouping with `collections` is simple and keeps the image small and dependency-free. Revisit if data grows to hundreds of thousands of rows or needs heavy reshaping.

## 2026-11-23 — Server-side HTML with CSS bars, no chart library

The stack was set to FastAPI + HTML. Jinja2 rendering plus CSS-width bars gives readable tables and bars with no JS framework or CDN, so the container runs offline. Revisit if interactive charts (filters, drill-down, hover) are requested.

## 2026-11-23 — Compute once at startup

The data is a static file; computing per request adds nothing. Revisit when data arrives continuously (then reload on file change or per request).

## 2026-11-23 — Drop exact duplicate rows, keep returns

Three rows were byte-identical repeats of the same invoice line (double entry). The one `RTR` row is a genuine return and belongs in net sales. See [data.md](data.md).

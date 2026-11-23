# Decision log

Newest first. Each entry: what was decided, why, and what would make us revisit it.

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

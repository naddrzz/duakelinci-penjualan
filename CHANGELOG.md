# Changelog

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

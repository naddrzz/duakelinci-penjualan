# Architecture

```
CSV ──load_sales()──▶ list[Sale] + CleaningReport ──build_report()──▶ report dict ──▶ 3 HTML pages (Jinja2)
     app/data.py                                     app/analysis.py              └─▶ GET /api/report (same dict as JSON)
```

- The default CSV is read **once at startup** (FastAPI lifespan in `app/main.py`) and kept in `app.state.default_report` and `app.state.report`. Users can also upload another 15-column CSV in the browser (`POST /api/upload`), which parses and cleans the file in memory (`load_sales_text`) and updates `app.state.report` without touching disk; `POST /api/report/reset` restores `app.state.default_report` immediately.
- A bad startup file (missing column, unparseable value, fewer than two months) fails startup instead of serving wrong numbers; a bad uploaded CSV returns `400`/`413` with an actionable Bahasa Indonesia message while keeping the active report intact.
- Every page is complete server-rendered HTML that works without JavaScript.

## Pages and templates

| Route | Template | Content |
|---|---|---|
| `GET /` | `ringkasan.html` | Page header, clean white KPIs, top region/brand leaderboards, 5-outlet watch preview, Telegram text with copy buttons, "Sekilas" facts, and the all-outlets table (search, filters, sort) |
| `GET /wilayah-merek?lihat=wilayah\|merek` | `wilayah_merek.html` | Four summary tiles, stacked share composition bar, and one wide full-rupiah table (region or brand) with the view picker (`form.view-switch`) inside the table card header; unknown `lihat` falls back to `wilayah` |
| `GET /outlet-terlemah` | `outlet_terlemah.html` | Sortable table of the 5 weakest outlets and their exact calculations at the top (`#weakest-table`), followed by side-by-side rule/formula and 5-step filtering funnel, and two alternative definitions for comparison (`report.weakest_analysis`) |

All three extend `base.html` (collapsible left sidebar `#sidebar` + compact mobile bar, `<main id="isi">`, data notes footer) and import shared macros from `_macros.html` (`pill`, `bar`, `sort_th`, `page_head`).

## Front end (`app/static/`)

- `app.css`: all styles and design tokens (light theme only).
- `app.js` (no libraries), loaded with `defer` on every page:
  - **Page features**, run by `initPage(root)` on load and after each page change: copy buttons (Clipboard API, `execCommand('copy')` fallback for plain-HTTP hosts), sorting on every `table.sortable`, search/filters/sort select on `#outlet-table` (rows carry `data-region`, `data-type`, `data-status`, `data-search`; sortable cells carry `data-value`), and the region/brand dropdown (toggles `[data-view]` sections and rewrites `?lihat=` with `history.replaceState`). The shell sidebar (`#sidebar`) supports hide/unhide via `[data-sidebar-toggle]` and `Ctrl+B`/`Cmd+B` (persisted in `localStorage` as `dk-sidebar`, initialized before first paint to prevent flash) and acts as a dismissible drawer with backdrop + `Escape` on viewports `<= 960px`.
  - **Router**: intercepts plain left-clicks on same-origin links to the three routes. It marks the nav item, shows a progress bar, fades the old content out (120 ms), shows a page-specific skeleton for at least `MIN_SKELETON_MS` (350 ms, so it never flashes), fetches the target page, swaps `<main>`, updates `document.title`, pushes history, then plays a one-off entrance animation. Focus moves to the new `<h1>`, or the page scrolls to the URL hash. Back/forward use the same path. Any fetch error falls back to a normal full page load.
  - Reduced motion: only opacity changes; the skeleton shimmer and progress animation are off.
- `asset_url()` (template global in `main.py`) appends the file's modification time to `app.css`/`app.js` URLs so browsers never run a stale copy.
- `MontserratVariable.woff2` and `InterVariable.woff2` (with SIL OFL licences) sit in `app/static/fonts/`, alongside the self-hosted brand logo (`logo-dk.png`) and square favicons (`favicon.ico`, `favicon.png`, `apple-touch-icon.png`). The app makes no external requests, so the container works offline.

## Endpoints

| Method & path | Returns |
|---|---|
| `GET /`, `/wilayah-merek`, `/outlet-terlemah` | HTML pages (see above); anything else is 404 |
| `GET /api/report` | The full active report as JSON (totals, regions, brands, outlets, weakest, weakest_analysis, data_quality, telegram_summary) |
| `POST /api/upload` | Accepts a custom `.csv` (`multipart/form-data` field `file` or `text/csv`, max 10 MiB), cleans & validates the 15 columns + >= 2 months in memory, and swaps `app.state.report` |
| `POST /api/report/reset` | Restores `app.state.report` back to `app.state.default_report` |
| `GET /api/sample-csv` | Downloads the bundled sample CSV (`data/dua_kelinci_sample_sales_sep_oct_2026.csv`) as a template |
| `GET /favicon.ico` | Multi-resolution (`16×16`, `32×32`, `48×48`) favicon generated from `logo-dk.png` |
| `GET /healthz` | `{"status": "ok"}`; used by the Docker `HEALTHCHECK` |
| `GET /static/...` | `app.css`, `app.js`, self-hosted fonts, logo & favicons |

## Configuration

| Setting | Where | Default |
|---|---|---|
| `DATA_PATH` | env var | `data/dua_kelinci_sample_sales_sep_oct_2026.csv` |
| Base materiality floor (`Q1`) | `adaptive_base_floor()` (`app/analysis.py`) | Exact unrounded 1st quartile of active base-month outlets (`Rp 4.927.700` on sample CSV) |
| `WEAK_OUTLET_COUNT` | `app/config.py` | 5 |
| `MAX_UPLOAD_BYTES` | `app/config.py` | 10 485 760 (10 MiB) |

## Deployment (Docker)

`Dockerfile`: `python:3.14-slim`, installs pinned `requirements.txt`, copies `app/` and `data/`, runs as non-root user `appuser` (uid 10001), serves uvicorn on port 8000, healthcheck hits `/healthz`.

Swap the data without rebuilding:

```bash
docker run --rm -p 8000:8000 \
  -v /path/to/new.csv:/data/sales.csv:ro -e DATA_PATH=/data/sales.csv \
  dua-kelinci-sales
```

The app has no authentication. Put it behind a reverse proxy or VPN if it is exposed beyond a trusted network.

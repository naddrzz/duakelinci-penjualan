# Architecture

```
CSV ──load_sales()──▶ list[Sale] + CleaningReport ──build_report()──▶ report dict ──▶ 3 HTML pages (Jinja2)
     app/data.py                                     app/analysis.py              └─▶ GET /api/report (same dict as JSON)
```

- The default CSV is read **once at startup** (FastAPI lifespan in `app/main.py`) and kept in `app.state.default_report` and `app.state.report`. Users can also upload another 15-column CSV in the browser (`POST /api/upload`), which parses and cleans the file in memory (`load_sales_text`) and updates `app.state.report` without touching disk; `POST /api/report/reset` restores `app.state.default_report` immediately.
- A bad startup file (missing column, unparseable value, fewer than two months) stops startup instead of serving wrong numbers; a bad uploaded CSV returns `400`/`413` with a clear Bahasa Indonesia error message while keeping the active report intact.
- Every page is complete server-rendered HTML that works without JavaScript.

## Pages and templates

| Route | Template | Content |
|---|---|---|
| `GET /` | `ringkasan.html` | Page header, 4-column KPI stat strip, one-paragraph **Telegram summary** with one-click copy paired with the 5 weakest outlets & highest/lowest highlights, and a searchable/filterable **Semua outlet** table |
| `GET /wilayah-merek?lihat=wilayah\|cabang\|merek\|salesman` | `wilayah_merek.html` | **Rincian penjualan** — tabbed full-rupiah table (`[data-dim-nav]`) across 4 dimensions (`wilayah`, `cabang`, `merek`, `salesman`) with inline search, share bars, and a `Total Keseluruhan` footer; unknown `lihat` falls back to `wilayah` |
| `GET /outlet-terlemah` | `outlet_terlemah.html` | Tab switch between `%` drop (`Kemerosotan %`) and rupiah drop (`Kehilangan Rp`), sortable decline table with a `Detail` button that opens a right-hand **outlet detail panel** (`#outlet-side-peek`: `»` close, `↑`/`↓` row navigation, `Salin detail`, invoice/carton/SKU summary, filterable SKU table `Semua / Berhenti / Jalan`, and per-salesman breakdown), followed by the `Q1` formula and 5-step filtering funnel |

All three extend `base.html` (collapsible left sidebar `#sidebar` + mobile bar, `<main id="isi">`, data notes footer) and import shared macros from `_macros.html` (`pill`, `bar`, `sort_th`, `page_head`).

## Front end (`app/static/`)

- `app.css`: all styles and design tokens (light theme only, mobile safe areas, `44×44px` touch targets, synchronized horizontal table scroll, slide-over detail panel, and mobile bottom-sheet upload dialog).
- `app.js` (no external libraries), loaded with `defer` on every page:
  - **Page features**, run by `initPage(root)` on load and after each page change: copy buttons (Clipboard API with `execCommand('copy')` fallback), sorting on every `table.sortable`, multi-token search/filters/sort select on `#outlet-table` (`initOutletTable`), inline search on breakdown and weakest tables (`initQuickTables`, `initLensSwitch`), sliding segmented controls (`initSegmented`), dimension tabs (`initViewSwitch`, toggling `[data-view]` sections and updating `?lihat=` via `history.replaceState`), and the slide-over outlet detail panel (`initSidePeek`, handling row stepping, `Semua / Berhenti / Jalan` SKU filters, `Escape`, and clipboard copy). Shell controls (`#sidebar` toggle via `[data-sidebar-toggle]` and `Ctrl+B`/`Cmd+B`, mobile drawer on `<= 960px`, and `#upload-dialog` CSV upload/reset via `initUploadDialog`) initialise once on `document`.
  - **Router**: intercepts plain left-clicks on same-origin links to the three routes, shows a progress bar and a page-shaped skeleton (`350 ms` minimum so fast local responses do not flicker), swaps `<main>`, updates `document.title`, and falls back to normal navigation on any error.
  - Reduced motion: disables shimmer and movement, leaving simple opacity fades.
- `asset_url()` (template global in `main.py`) appends each static file's modification time so browsers pick up updates immediately.
- `MontserratVariable.woff2` and `InterVariable.woff2` (with SIL OFL licences) sit in `app/static/fonts/`, alongside `logo-dk.png` and favicons (`favicon.ico`, `favicon.png`, `apple-touch-icon.png`). Zero external requests are made.

## Endpoints

| Method & path | Returns |
|---|---|
| `GET /`, `/wilayah-merek`, `/outlet-terlemah` | HTML pages (see above); anything else is 404 |
| `GET /api/report` | The full active report as JSON (totals, regions, branches, brands, salesmen, outlets, weakest, weakest_analysis, data_quality, telegram_summary) |
| `POST /api/upload` | Accepts a custom `.csv` (`multipart/form-data` field `file` or `text/csv`, max 10 MiB), cleans & validates the 15 columns + `>= 2` months in memory, and swaps `app.state.report` |
| `POST /api/report/reset` | Restores `app.state.report` back to `app.state.default_report` |
| `GET /api/sample-csv` | Downloads the bundled sample CSV (`data/dua_kelinci_sample_sales_sep_oct_2026.csv`) |
| `GET /favicon.ico` | Multi-resolution (`16×16`, `32×32`, `48×48`) favicon |
| `GET /healthz` | `{"status": "ok"}`; used by the Docker `HEALTHCHECK` |
| `GET /static/...` | `app.css`, `app.js`, self-hosted fonts, logo & favicons |

## Configuration

| Setting | Where | Default |
|---|---|---|
| `DATA_PATH` | env var | `data/dua_kelinci_sample_sales_sep_oct_2026.csv` |
| `PORT` / `HOST_PORT` | env var (`Dockerfile` / `compose.yaml`) | `8000` |
| Minimum base-month sales (`Q1`) | `adaptive_base_floor()` (`app/analysis.py`) | 25th percentile (`Q1`) of active base-month outlets (`Rp 4.927.700` on sample CSV) |
| `WEAK_OUTLET_COUNT` | `app/config.py` | 5 |
| `MAX_UPLOAD_BYTES` | `app/config.py` | 10 485 760 (10 MiB) |

## Deployment (Docker)

- `Dockerfile`: `python:3.14-slim`, whitelist `.dockerignore`, installs pinned `requirements.txt`, copies `app/` and `data/` with world-readable permissions, runs as non-root `appuser` (uid `10001`), verifies bundled fonts/icons/templates/CSV at build time, serves uvicorn on `${PORT:-8000}`, and checks `/healthz` via `HEALTHCHECK`.
- `compose.yaml`: runs the container with `read_only: true`, `tmpfs: ["/tmp"]`, and `restart: unless-stopped` (`docker compose up -d --build`).

Swap the data without rebuilding:

```bash
docker run --rm -p 8000:8000 \
  -v /path/to/new.csv:/data/sales.csv:ro -e DATA_PATH=/data/sales.csv \
  dua-kelinci-sales
```

The app has no login layer; place it behind a reverse proxy or VPN if exposed outside a local or internal network.

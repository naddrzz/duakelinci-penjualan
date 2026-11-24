# AGENTS.md

## Project snapshot

Single-package, three-page FastAPI + Jinja2 web app that turns a 15-column sales CSV into a commercial dashboard for PT Dua Kelinci:
1. **Ringkasan** (`/`): KPI stat strip, concise Telegram summary (`telegram_summary()`), 5-outlet watch list, highest/lowest highlights, and a searchable/filterable directory of all outlets.
2. **Rincian penjualan** (`/wilayah-merek?lihat=wilayah|cabang|merek|salesman`): numbered full-rupiah tabbed tables across region, city branch, brand, and salesman.
3. **Outlet terlemah** (`/outlet-terlemah`): `%` drop (`Kemerosotan %` above the 25th-percentile `Q1` cutoff) and Rupiah drop (`Kehilangan Rp`) tabs, a slide-over outlet detail panel (`#outlet-side-peek`) with SKU-level `Semua / Berhenti / Jalan` status and per-salesman breakdown, plus the `Q1` formula and 5-step filtering funnel.

UI copy and Telegram text are **Bahasa Indonesia**; code, identifiers, commits, and docs are **English**. All fonts, logos, and favicons are self-hosted so the app runs 100% offline.

## Setup, test & deploy commands

```bash
pip install -r requirements-dev.txt
python -m pytest                                  # 43 tests; must be green before finishing
uvicorn app.main:app --reload                     # http://127.0.0.1:8000
docker compose up -d --build                      # optional container run on port 8000
```

## Architecture & JIT file map

`CSV` → `app/data.py` (`load_sales`, `load_sales_text`) → `app/analysis.py` (`build_report`) → `app/main.py` (`app.state.report`, HTML + JSON routes).

- **Data & validation**: `app/data.py` — 15-column schema check, `,`/`;` delimiter detection, whitespace trimming, region alias normalisation, exact-row deduplication, return preservation.
- **Metrics & attribution**: `app/analysis.py` — 25th-percentile `Q1` base-sales cutoff (`adaptive_base_floor`), `Region → Branch → Salesman → Outlet [ID]` rollups, per-outlet SKU status (`berhenti`/`turun`/`tumbuh`/`baru`/`stabil`), `%` and Rupiah drop rankings, and one-paragraph `telegram_summary()`.
- **HTTP & state**: `app/main.py` — serves `/`, `/wilayah-merek`, `/outlet-terlemah`, `GET /api/report`, `POST /api/upload` (stdlib `BytesParser`, 10 MiB cap, in-memory report swap), `POST /api/report/reset` (restores `app.state.default_report`), `GET /api/sample-csv`, `GET /favicon.ico`, and `GET /healthz`.
- **Formatting & config**: `app/formatting.py` (Indonesian Rupiah, short Rupiah, Telegram Rupiah + HTML preview, `%`, month/date labels); `app/config.py` (`DATA_PATH`, `WEAK_OUTLET_COUNT`, `MAX_UPLOAD_BYTES`).
- **Templates**: `app/templates/base.html` (shell, collapsible `#sidebar`, sticky `.mobile-bar`, `#upload-dialog`, data notes footer), `_macros.html`, `ringkasan.html`, `wilayah_merek.html`, `outlet_terlemah.html`.
- **Frontend assets**: `app/static/app.css` (light-only tokens, responsive grids, tables, detail panel, bottom-sheet dialog) and `app/static/app.js` (same-origin skeleton router, sorting, multi-token search, filters, segmented indicator, `[data-dim-nav]` tabs, `#outlet-side-peek`, CSV upload modal). Fonts + OFL licences live in `app/static/fonts/`.
- **Tests**: `tests/test_data.py` (cleaning), `tests/test_analysis.py` (metrics, `Q1` cutoff, SKU & salesman breakdown, one-paragraph Telegram summary), `tests/test_api.py` (routes, upload/reset, offline assets, zero hardcoded sample leakage).

### Quick find commands

```bash
git grep -n "def " app/ tests/                    # list Python functions and tests
git grep -n "@app\.\(get\|post\)" app/main.py     # list HTTP endpoints
git grep -n "function init" app/static/app.js     # list client-side initialisers
python -m pytest -k "weakest or custom_csv" -v    # run targeted test slice
```

## Business rules & context pointers (single source of truth)

Treat these as product decisions. Change them only when asked, and update the matching doc in the same edit:

- **CSV schema, region aliases, dedupe & return rules** → read [docs/data.md](docs/data.md) before editing `app/data.py`.
- **Metric formulas, `Q1` weakest-outlet rule, SKU/salesman breakdown & Telegram paragraph** → read [docs/metrics.md](docs/metrics.md) before editing `app/analysis.py` or `app/config.py`.
- **Data flow, routes, frontend router/drawer/detail panel & Docker runtime** → read [docs/architecture.md](docs/architecture.md) before editing `app/main.py` or `app/static/`.
- **Engineering & UI rationale** → read [docs/decisions.md](docs/decisions.md); append a dated entry for comparable trade-offs.

## Change matrix

| When you change | Also update |
|---|---|
| A cleaning rule, delimiter rule or region alias | `docs/data.md`, `tests/test_data.py` |
| A metric, `Q1` cutoff, SKU/salesman breakdown or Telegram format | `docs/metrics.md`, `docs/decisions.md`, `tests/test_analysis.py` |
| The bundled sample CSV | Reference numbers in `tests/test_analysis.py` and `docs/metrics.md` |
| An endpoint, env var, upload limit or `Dockerfile` | `docs/architecture.md`, `README.md`, `tests/test_api.py` |
| Colors, typography or layout (`app.css`, templates) | Verify light-theme WCAG AA contrast (`>= 4.5:1` text, `>= 3:1` controls/bars), `320px` width with zero horizontal page scroll across all 3 pages, and `44×44px` non-overlapping coarse-pointer targets |
| Table columns in `ringkasan.html`, `wilayah_merek.html`, or `outlet_terlemah.html` | `colspan` on `.empty-row`, sort `<option value="index:dir">` indexes in `ringkasan.html`, and `.sticky-col` horizontal scroll sync (`.numbered-table` and `@media (max-width: 720px)`) |
| Outlet detail panel (`#outlet-side-peek`) or upload dialog (`#upload-dialog`) | `initSidePeek` / `initUploadDialog` in `app.js`, keyboard `Escape`/focus handling, mobile `<= 520px` sheet layout, and `tests/test_api.py` |
| Add, rename or remove a page | `SAFE_PATHS` + route in `app/main.py`, `.sidenav` in `base.html`, `PAGE_KEYS` + `SKELETONS` in `app.js`, `tests/test_api.py`, `docs/architecture.md` |
| A page's macro layout | Matching placeholder in `SKELETONS` (`app/static/app.js`) |
| Anything user-visible | `CHANGELOG.md` |

## Conventions & guardrails

- **Zero hardcoded data**: every rendered label, period, region, branch, salesman, outlet, and SKU must come from `app.state.report` (`test_custom_csv_has_zero_hardcoded_sample_leakage` enforces this against custom CSV uploads).
- **Aggregate outlets by `outlet_id`**: store names repeat across cities/branches (e.g. *Toko Sinar Abadi*).
- **Integer Rupiah end to end**: keep money as `int` in `data.py` and `analysis.py`; format only at the template/Telegram edge via `app/formatting.py`.
- **Dynamic period comparison**: always compare the last two months present in the dataset (`base` → `current`) so multi-month or new-year CSVs work without code changes.
- **Mobile-native & offline discipline**: never add external network requests (CDNs, Google Fonts, external icons); never disable pinch-zoom (`user-scalable=no` / `maximum-scale=1`); keep inputs `>= 16px` on coarse pointers, gate `:hover` behind `@media (hover: hover) and (pointer: fine)`, and gate programmatic input `.focus()` behind `!matchMedia("(pointer: coarse)").matches`.
- **Minimal dependencies**: stick to the Python stdlib plus pinned `fastapi`, `uvicorn`, and `jinja2` in `requirements.txt` unless strictly necessary.

## Definition of done

1. `python -m pytest` passes completely (`0` failures).
2. Custom CSV upload/reset (`test_custom_csv_has_zero_hardcoded_sample_leakage`) passes with zero sample-data leakage.
3. No horizontal document overflow (`clientWidth === scrollWidth`) at `320px`, `375px`, and `1366px` across `/`, `/wilayah-merek`, and `/outlet-terlemah`.
4. Companion docs (`docs/*.md`, `README.md`, `CHANGELOG.md`) are updated per the change matrix above.

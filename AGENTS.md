# AGENTS.md

Three-page FastAPI web app that summarises Dua Kelinci sales from a CSV for a sales manager: net sales per region and brand, the 5 weakest outlets, and a copy-ready Telegram paragraph. The UI and Telegram text are Bahasa Indonesia; code and docs are English.

## Commands

```bash
pip install -r requirements-dev.txt
python -m pytest                       # must be green before you finish
uvicorn app.main:app --reload          # http://127.0.0.1:8000
docker build -t dua-kelinci-sales .
docker run --rm -p 8000:8000 dua-kelinci-sales
```

## Map

`app/data.py` loads and cleans the CSV → `app/analysis.py` builds one report dict → `app/main.py` serves it as three HTML pages (`/` → `ringkasan.html`, `/wilayah-merek` → `wilayah_merek.html`, `/outlet-terlemah` → `outlet_terlemah.html`, all extending `base.html`) and as JSON (`/api/report`). `app/static/app.css` and `app/static/app.js` hold all styles and behaviour, including the page-transition router; see [docs/architecture.md](docs/architecture.md#front-end-appstatic) before editing it. `app/formatting.py` holds Indonesian number/month formatting. `app/static/fonts/` holds the self-hosted Inter + Montserrat variable fonts and their OFL licences, alongside `logo-dk.png` in `app/static/`; keep the app free of external requests. `app/config.py` holds the data path and business thresholds.

## Business rules (single source of truth)

These are decisions, not implementation details. Change them only when the user asks, and change the doc in the same edit.

- Cleaning rules (region aliases, dedupe, returns, trimming) → read [docs/data.md](docs/data.md) before touching `app/data.py`.
- Metric definitions, the **weakest outlet** rule and the Telegram template → read [docs/metrics.md](docs/metrics.md) before touching `app/analysis.py` or `app/config.py`.
- Why the stack looks the way it does (stdlib over pandas, CSS bars, server-side HTML) → [docs/decisions.md](docs/decisions.md). Add an entry when you make a comparable choice.
- Data flow, endpoints, deployment → [docs/architecture.md](docs/architecture.md).

## When you change something

| You change | Also update |
|---|---|
| A cleaning rule or region alias | `docs/data.md`, `tests/test_data.py` |
| A metric, threshold or the weakest-outlet rule | `docs/metrics.md`, `docs/decisions.md`, `tests/test_analysis.py` |
| The sample CSV | reference numbers in `tests/test_analysis.py` and `docs/metrics.md` |
| An endpoint, env var or the Dockerfile | `docs/architecture.md`, `README.md` |
| Colors or layout (`app/static/app.css`, templates) | re-check WCAG AA contrast (light theme only), 320px width with no horizontal page scroll on all three pages, and the a11y list in `docs/decisions.md` |
| Outlet table columns (`ringkasan.html`) | the column indexes (the sort `<select>` sits in `.result-line`, not the toolbar) in the "Urutkan" `<option value="index:dir">` list and `colspan` of the empty-state row |
| Add, rename or remove a page | the route in `app/main.py`, the nav list in `base.html`, `PAGE_KEYS` and `SKELETONS` in `app.js`, `tests/test_api.py`, `docs/architecture.md` |
| A page's layout | its skeleton in `SKELETONS` (`app.js`) so the placeholder still matches the loaded page |
| Anything user-visible | `CHANGELOG.md` |

## Conventions

- Aggregate outlets by `outlet_id`; outlet names repeat across outlets.
- Money is integer rupiah end to end; format only at the edge with `app/formatting.py`.
- Comparisons always use the last two months present in the data (`base` → `current`), so new months need no code change.
- Add dependencies only when the stdlib or the installed ones cannot do the job; pin versions in `requirements.txt`.

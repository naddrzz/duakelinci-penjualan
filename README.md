# Dua Kelinci Sales Summary

A three-page web app for the sales manager, built from `data/dua_kelinci_sample_sales_sep_oct_2026.csv`:

1. **Ringkasan** (`/`): headline numbers, a copy-ready **Telegram summary** (nothing is sent) and a searchable, filterable, sortable table of **all outlets**.
2. **Wilayah & merek** (`/wilayah-merek`): pick **region** or **brand** from a dropdown to see one wide table of net sales, Sep vs Okt.
3. **Outlet terlemah** (`/outlet-terlemah`): the **5 weakest outlets** (largest % drop from September to October among outlets that sold at least Rp 5 jt in September), with the step-by-step filtering and each outlet's calculation. Why this rule: [docs/metrics.md](docs/metrics.md).

## Run locally

```bash
pip install -r requirements-dev.txt
python -m pytest
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. JSON is at `/api/report`. To analyse another CSV with the same 15-column format, click **Unggah CSV** in the sidebar (you can also download the sample CSV template from the dialog or reset back to the default sample at any time).

## Run with Docker

```bash
docker build -t dua-kelinci-sales .
docker run -d --name dua-kelinci-sales -p 8000:8000 dua-kelinci-sales
```

Use another CSV (same columns) without rebuilding:

```bash
docker run -d -p 8000:8000 -v /path/to/new.csv:/data/sales.csv:ro -e DATA_PATH=/data/sales.csv dua-kelinci-sales
```

## Docs

- [docs/data.md](docs/data.md): columns, data-quality issues found, cleaning rules
- [docs/metrics.md](docs/metrics.md): metric definitions, weakest-outlet rule, Telegram template, reference numbers
- [docs/architecture.md](docs/architecture.md): data flow, endpoints, config, deployment
- [docs/decisions.md](docs/decisions.md): why things are built this way
- [AGENTS.md](AGENTS.md): instructions for AI coding agents
- [CHANGELOG.md](CHANGELOG.md)

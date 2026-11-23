# Data: source file and cleaning rules

Source: `data/dua_kelinci_sample_sales_sep_oct_2026.csv` (override at startup with the `DATA_PATH` env var, or upload another CSV with the same 15 columns directly from the UI via `POST /api/upload`). Both comma-delimited (`,`) and semicolon-delimited (`;`, common in Indonesian Excel exports) UTF-8 CSVs are accepted. One row = one SKU line on one invoice. Implemented in `app/data.py`; tested in `tests/test_data.py`.

## Columns

| Column | Type | Meaning |
|---|---|---|
| `date` | ISO date | Invoice date (2026-09-01 … 2026-10-31) |
| `invoice_no` | text | `INV…` = sale, `RTR…` = return |
| `region` | text | Sales region; 6 canonical values (see aliases) |
| `branch` | text | Branch (city) within the region; 13 values |
| `outlet_id` | text | Unique outlet key; 52 outlets |
| `outlet_name` | text | Display name; **not unique** (e.g. `Toko Sinar Abadi` is 3 outlets) |
| `outlet_type` | text | Grosir, Toko Kelontong, Warung, Minimarket |
| `salesman` | text | Salesman name; may be blank |
| `brand` | text | 8 brands |
| `sku` | text | 13 SKUs; each maps to one brand and one fixed price |
| `qty_carton` | int | Cartons; negative on returns |
| `price_per_carton_idr` | int | List price per carton |
| `gross_sales_idr` | int | `qty_carton × price_per_carton_idr` |
| `discount_idr` | int | 0, 2, 3 or 5 % of gross |
| `net_sales_idr` | int | `gross − discount`. **The metric used everywhere.** |

## Cleaning rules (applied in this order)

1. **Trim** surrounding whitespace on every field (4 rows had a trailing space in `outlet_name`).
2. **Normalise region** case-insensitively through `REGIONS` in `app/data.py`; `Jabar` is an alias of `Jawa Barat` (10 rows changed). An unknown region is kept in Title Case and listed in the report's `unknown_regions`, which the page footer shows.
3. **Blank salesman** becomes `(unassigned)` (5 rows). No feature uses salesman today.
4. **Parse** date and integer columns; a missing column or unparseable value stops startup with a `ValueError` naming the line.
5. **Check amounts**: rows where gross ≠ qty × price or net ≠ gross − discount are counted in `amount_mismatches` and shown in the footer; `net_sales_idr` is still used. (0 rows today.)
6. **Drop exact duplicates** after steps 1–3 (3 rows, Rp 2.070.900: INV500201, INV500386, INV500791 were each entered twice).
7. **Keep returns**: `RTR900001` (−2 cartons, −Rp 528.000) stays in, because net sales should be net of returns.

Result on the sample file: 1,891 raw rows → 1,888 clean rows, net sales Rp 1.725.966.000.

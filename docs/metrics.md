# Metrics

Implemented in `app/analysis.py`; defaults in `app/config.py`; tested in `tests/test_analysis.py`.

## Shared definitions

- **Sales** always means `net_sales_idr` after cleaning (see [data.md](data.md)): after discount and net of returns.
- **Period**: every month present in the data. **Base** and **current** are the last two months (sample file: Sep 2026 → Okt 2026). With fewer than two months the app refuses to start.
- **Change %** = `(current − base) / base × 100`; undefined (shown as `"baru"`) when `base <= 0`.

## 1. Sales per region, branch, brand, and salesman

For each **region**, **city branch**, **brand**, and **salesman**: sales per month, total, rupiah difference, change %, and share of grand total, sorted from highest to lowest total:
- **Region (`report.regions`)**: includes its city branches (`branches`, `top_branch`, `branches_label`), outlet count, and top salesman. Highest on sample data: `Jabodetabek` (`Rp 495.827.800`, `28,7%`), covering `Tangerang` (`Rp 249.019.600`), `Jakarta Barat` (`Rp 168.834.700`), and `Bekasi` (`Rp 77.973.500`).
- **Branch (`report.branches`)**: 13 city branches with parent `region`, outlet count, and `salesmen_label`. Highest: `Tangerang` (`Rp 249.019.600`, `14,4%`); lowest: `Banjarmasin` (`Rp 31.969.000`, `1,9%`).
- **Brand (`report.brands`)**: 8 brands with top region, branch, and salesman. Highest: `Kacang Dua Kelinci` (`Rp 739.781.900`, `42,9%`); lowest: `Roni` (`Rp 34.399.200`, `2,0%`).
- **Salesman (`report.salesmen` & `report.named_salesmen`)**: 26 named salesmen plus a `Belum tercatat` row for the 5 blank-salesman lines so table totals still add up to `100%`. Highest named salesman: `Citra` (`Tangerang, Jabodetabek`, `Rp 136.587.300`, `+17,1%`); lowest: `Bayu` (`Banjarmasin, Kalimantan`, `Rp 13.084.600`, `+41,5%`); largest % drop: `Teguh` (`Medan, Sumatera`, `−44,2%` / `−Rp 27.484.800`).

## 2. Weakest outlets

The brief leaves "weakest" open to interpretation. Ranking by lowest total flags tiny warungs that are actually growing, while ranking by raw `%` drop without a minimum size lets a small warung that skipped one order dominate the list.

**Main ranking (`report.weakest` — steepest `%` drop above the `Q1` minimum):**
1. **Exclude new outlets** (`base <= 0`), since they have no base-month sales to compare against (`1` outlet on the sample CSV: `OUT1047`).
2. **Exclude the smallest 25% of base-month outlets (`< Q1`)** via `adaptive_base_floor()`. Specifically, take the 25th percentile (`Q1`, position `0.25 × (N + 1)`) of active base-month sales using `math.ceil(q1)` without rounding to arbitrary multiples. On the sample CSV (`51` active outlets in September), `0.25 × (51 + 1) = 13th` smallest outlet (`OUT1021 Toko Mandiri`), giving **`Q1 = Rp 4.927.700`** (`12` small outlets excluded, `39` eligible). Because `Q1` is computed from the data itself, uploaded CSVs with smaller or larger numbers get a proportional cutoff automatically (or `0` when `< 4` active outlets exist).
3. **Take the 5 steepest `%` declines** (`change_pct < 0`, ties broken by rupiah drop). Each outlet also tracks invoice count (`base_invoices -> current_invoices`, counting positive sales invoices only), carton volume, SKU movement (`berhenti`, `turun`, `tumbuh`, `baru`, `stabil`), and per-salesman sales change.

**Secondary view (`report.weakest_analysis.revenue_at_risk` — largest Rupiah drop):**
- Ranks active declining outlets by rupiah loss (`change_idr` ascending). Percentage drop catches mid-size stores losing half their order volume, whereas rupiah drop surfaces large wholesalers (`Grosir Sentosa −Rp 31,6 jt`, `Grosir Sumber Alam −Rp 24,3 jt`) that account for `68,5%` of total lost rupiah across all declining stores. Both views are available via a tab switch on `/outlet-terlemah`.

**Result on the sample data (`%` drop view):**

| # | Outlet | Branch | Invoices / SKUs (Sep→Okt) | Sep | Okt | Change |
|---|---|---|---|---|---|---|
| 1 | OUT1043 Minimarket Sido Muncul | Palembang | 5→3 inv · 9→5 SKU | 9.181.700 | 2.873.700 | −68,7 % |
| 2 | OUT1022 Toko Bintang | Semarang | 6→4 inv · 10→5 SKU | 8.764.300 | 3.223.100 | −63,2 % |
| 3 | OUT1041 Toko Anugerah | Palembang | 12→6 inv · 10→8 SKU | 12.494.900 | 5.909.600 | −52,7 % |
| 4 | OUT1048 Toko Mekar | Banjarmasin | 5→3 inv · 8→3 SKU | 5.143.700 | 2.473.900 | −51,9 % |
| 5 | OUT1001 Toko Sinar Abadi | Jakarta Barat | 6→3 inv · 9→7 SKU | 6.929.900 | 3.579.000 | −48,4 % |

## 3. Telegram summary (`telegram_summary()`)

Produces a **single paragraph** in Bahasa Indonesia (`"\n" not in text`) ready for a sales manager to read in Telegram:
- **Structure**: current-month net sales and month-over-month change, regional growth vs decline summary (how many of the regions fell and which fell steepest), the 5 steepest `%` drop outlets with tap-to-copy `` `OUTxxxx` `` codes and the salesman driving each drop, and the largest Rupiah drops on big wholesaler accounts.
- **Formatting**: restrained `**bold**` on the headline figure and the two action leads (`**Lima outlet turun terdalam:**`, `**Rupiah terbesar hilang**`), `` `OUTxxxx` `` monospace codes, and EYD V prose currency (`Rp878,4 juta`, `Rp31,6 juta`). On the web page, `tg_preview_html()` renders the paragraph cleanly without raw Markdown symbols.

Sample output:

```text
Penjualan bersih Oktober 2026 **Rp878,4 juta**, naik 3,6% dari September. Jawa Timur naik 92%, tetapi empat dari enam wilayah turun, terdalam Jawa Barat (14%). **Lima outlet turun terdalam:** Minimarket Sido Muncul `OUT1043` Palembang (69%, sales Zaki), Toko Bintang `OUT1022` Semarang (63%, sales Lestari), Toko Anugerah `OUT1041` Palembang (53%, sales Yudi), Toko Mekar `OUT1048` Banjarmasin (52%, sales Agus), dan Toko Sinar Abadi `OUT1001` Jakarta Barat (48%, sales Andi). **Rupiah terbesar hilang** di Grosir Sentosa Bandung (Rp31,6 juta, sales Gita) dan Grosir Sumber Alam Solo (Rp24,3 juta, sales Nanda).
```

## Reference numbers (sample file)

| Figure | Value |
|---|---|
| Net sales total | Rp 1.725.966.000 |
| Sep / Okt | Rp 847.517.400 / Rp 878.448.600 (+3,6 %) |
| Best region | Jabodetabek Rp 495.827.800 (28,7 %) |
| Best brand | Kacang Dua Kelinci Rp 739.781.900 (42,9 %) |
| Outlets / invoices / cartons | 52 / 824 / 8.745 |

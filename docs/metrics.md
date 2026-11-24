# Metrics

Implemented in `app/analysis.py`; thresholds in `app/config.py`; tested in `tests/test_analysis.py`.

## Shared definitions

- **Sales** always means `net_sales_idr` after cleaning (see [data.md](data.md)): after discount and net of returns.
- **Period**: every month present in the data. **Base** and **current** are the last two months (today: Sep 2026 → Okt 2026). With fewer than two months the app refuses to start.
- **Change %** = `(current − base) / base × 100`; undefined (shown as "baru") when base ≤ 0.

## 1. Sales per region, branch, brand, and salesman

For each **region** (group area), **city branch**, **brand**, and **salesman**: sales per month, total, rupiah diff, change %, and share of grand total, sorted by total (highest first):
- **Region (`report.regions`)**: includes its child city branches (`branches`, `top_branch`, `branches_label`), outlet count, and top salesman. Best region on sample data: `Jabodetabek` (`Rp 495.827.800`, `28,7%`), comprising `Tangerang` (`Rp 249.019.600`), `Jakarta Barat` (`Rp 168.834.700`), and `Bekasi` (`Rp 77.973.500`).
- **Branch (`report.branches`)**: 13 city branches with parent `region`, outlet count, and `salesmen_label`. Highest: `Tangerang` (`Rp 249.019.600`, `14,4%`); lowest: `Banjarmasin` (`Rp 31.969.000`, `1,9%`).
- **Brand (`report.brands`)**: 8 brands with strongest region, branch, and salesman. Highest: `Kacang Dua Kelinci` (`Rp 739.781.900`, `42,9%`); lowest: `Roni` (`Rp 34.399.200`, `2,0%`).
- **Salesman (`report.salesmen` & `report.named_salesmen`)**: 26 named salesmen (plus transparent `Belum tercatat` row for the 5 blank-salesman lines so table totals reconcile to `100%`). Highest named salesman: `Citra` (`Tangerang, Jabodetabek`, `Rp 136.587.300`, `+17,1%`); lowest named salesman: `Bayu` (`Banjarmasin, Kalimantan`, `Rp 13.084.600`, `+41,5%`); steepest contraction: `Teguh` (`Medan, Sumatera`, `−44,2%` / `−Rp 27.484.800`).

## 2. Weakest outlets (Dual-Lens FMCG + Adaptive Q1 Floor)

Full primary-source justification lives in [research-weakest-outlet-and-telegram.md](research-weakest-outlet-and-telegram.md).

**Primary lens (`report.weakest` — Steepest % Erosion on Comparable Stores >= Q1):**
- Exclude new outlets (`base <= 0`), matching the retail *Comparable / Same-Store Sales* standard.
- Compute an **exact, unrounded base-month materiality floor** from the **1st quartile (`Q1 / P25`, position `0.25 × (N + 1)`, equivalent to Excel `=QUARTILE.EXC`)** of active base-month outlets (`adaptive_base_floor()`), using `math.ceil(q1)` so integer rupiah comparisons `base >= floor` are mathematically identical to `base >= q1` even when linear interpolation produces fractional rupiah. No intermediate rounding to clean multiples is applied, so outlets near the quartile boundary are never misclassified. On the sample CSV (`51` active outlets), `0.25 × (51 + 1) = 13th` ascending outlet (`OUT1021 Toko Mandiri`), giving **`Q1 = Rp 4.927.700`** (`12` bottom-quartile outlets `< Q1` excluded, `39` outlets `>= Q1` eligible, `21` declining). On custom uploaded CSVs of any currency scale, `Q1` adapts automatically (and returns `0` when `< 4` active outlets exist).
- Among eligible declining outlets (`change_pct < 0`), take the `WEAK_OUTLET_COUNT` (5) steepest `%` declines (ties break on rupiah drop). Each outlet also tracks positive-quantity sales activity (`base_invoices -> current_invoices` and `base_skus -> current_skus`, excluding negative return credit notes from order-frequency counts).

**Complementary lens (`report.weakest_analysis.revenue_at_risk` — Largest Rupiah Contraction / Revenue-at-Risk):**
- Ranks active declining outlets by absolute rupiah loss (`change_idr` ascending). While the `%` lens catches mid-size retail shops losing 48–69% of velocity (`21,0%` of total lost rupiah), the Rupiah lens catches key wholesaler accounts (`Grosir Sentosa −Rp 31,6 jt`, `Grosir Sumber Alam −Rp 24,3 jt`) that drive **`68,5%`** of the network's total `Rp 116,4 jt` decline.
- Cross-validated against **Empirical Bayes Shrinkage** (`report.weakest_analysis.empirical_bayes`, prior weight $C = \text{median base sales Rp 8.491.500}$), which surfaces both retail steep drops and top wholesaler drops simultaneously.

**Result on the sample data (Primary % Erosion Lens):**

| # | Outlet | Branch | Invoices / SKUs (Sep→Okt) | Sep | Okt | Change |
|---|---|---|---|---|---|---|
| 1 | OUT1043 Minimarket Sido Muncul | Palembang | 5→3 inv · 9→5 SKU | 9.181.700 | 2.873.700 | −68,7 % |
| 2 | OUT1022 Toko Bintang | Semarang | 6→4 inv · 10→5 SKU | 8.764.300 | 3.223.100 | −63,2 % |
| 3 | OUT1041 Toko Anugerah | Palembang | 12→6 inv · 10→8 SKU | 12.494.900 | 5.909.600 | −52,7 % |
| 4 | OUT1048 Toko Mekar | Banjarmasin | 5→3 inv · 8→3 SKU | 5.143.700 | 2.473.900 | −51,9 % |
| 5 | OUT1001 Toko Sinar Abadi | Jakarta Barat | 6→3 inv · 9→7 SKU | 6.929.900 | 3.579.000 | −48,4 % |

## 3. Telegram summary (Chat-First Stacked Briefing — EYD V & Native Entities)

Full primary-source research on Telegram client paste mechanics (`**bold**` & tap-to-copy `` `code` `` entities, `U+00A0` non-breaking unit glue) and Indonesian readability (`EYD V`, *Narabahasa*, Indonesian UX Writing) lives in [research-telegram-formatting-and-bahasa-indonesia.md](research-telegram-formatting-and-bahasa-indonesia.md).

Designed for effortless 5-second mobile & desktop scanning inside Telegram chat bubbles (`telegram_summary()`):
- **Telegram-native hierarchy**: `**...**` converts into native `messageEntityBold` on paste/send across Telegram Desktop, Android, and iOS; `` `OUTxxxx` `` converts into a tap-to-copy `messageEntityCode` badge so managers can tap any outlet code to copy it straight into the dashboard search bar.
- **EYD V tight `Rp` + `U+00A0` unit glue (`rp_tg`)**: formats compact amounts as `Rp1,73\u00A0miliar`, `Rp847,5\u00A0jt`, `−Rp6,3\u00A0jt` so neither `Rp` nor `jt`/`rb` ever breaks onto an orphan line on narrow mobile screens.
- **Stacked short micro-lines & natural Bahasa Indonesia**: separates each item by a blank line and gives each semantic facet (store + ID + city, amount + `%`, invoice count, salesman + drop driver) its own short line without meta-labels (`Perbandingan:`) or repetitive `dari total`.

Sample output:

```text
**Laporan Penjualan Dua Kelinci**
Periode Sep–Okt 2026

**Capaian Utama**
Omzet bersih **Rp1,73 miliar** (naik 3,6%)
Sep Rp847,5 jt → Okt Rp878,4 jt

• Wilayah #1: **Jabodetabek**
  Rp495,8 jt (28,7%)
  Tangerang Rp249,0 jt · Jakarta Barat Rp168,8 jt · Bekasi Rp78,0 jt
...
**5 Outlet Turun Terdalam (Sep → Okt)**

1. **Minimarket Sido Muncul** `OUT1043` · Palembang
   Rp9,2 jt → Rp2,9 jt (**−69%** · −Rp6,3 jt)
   5→3 faktur
   Sales Zaki, Yudi (Zaki turun Rp6,8 jt)
...
```

## Reference numbers (sample file)

| Figure | Value |
|---|---|
| Net sales total | Rp 1.725.966.000 |
| Sep / Okt | Rp 847.517.400 / Rp 878.448.600 (+3,6 %) |
| Best region | Jabodetabek Rp 495.827.800 (28,7 %) |
| Best brand | Kacang Dua Kelinci Rp 739.781.900 (42,9 %) |
| Outlets / invoices / cartons | 52 / 824 / 8.745 |

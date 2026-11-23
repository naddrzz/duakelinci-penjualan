# Metrics

Implemented in `app/analysis.py`; thresholds in `app/config.py`; tested in `tests/test_analysis.py`.

## Shared definitions

- **Sales** always means `net_sales_idr` after cleaning (see [data.md](data.md)): after discount and net of returns.
- **Period**: every month present in the data. **Base** and **current** are the last two months (today: Sep 2026 → Okt 2026). With fewer than two months the app refuses to start.
- **Change %** = `(current − base) / base × 100`; undefined (shown as "baru") when base ≤ 0.

## 1. Sales per region and brand

For each region and each brand: sales per month, total, change %, and share of grand total. Sorted by total, highest first. The first row is the "best" region/brand used in the Telegram text.

## 2. Weakest outlets (Dual-Lens FMCG + Adaptive Q1 Floor)

Full primary-source justification lives in [research-weakest-outlet-and-telegram.md](research-weakest-outlet-and-telegram.md).

**Primary lens (`report.weakest` — Steepest % Erosion on Comparable Stores >= Q1):**
- Exclude new outlets (`base <= 0`), matching the retail *Comparable / Same-Store Sales* standard.
- Compute an **exact, unrounded base-month materiality floor** from the **1st quartile (`Q1 / P25`, position `0.25 × (N + 1)`)** of active base-month outlets (`adaptive_base_floor()`). No intermediate rounding is applied, so outlets near the quartile boundary are never misclassified. On the sample CSV (`51` active outlets), `0.25 × (51 + 1) = 13th` ascending outlet (`OUT1021 Toko Mandiri`), giving **`Q1 = Rp 4.927.700`** (`12` bottom-quartile outlets `< Q1` excluded, `39` outlets `>= Q1` eligible, `21` declining). On custom uploaded CSVs of any currency scale, `Q1` adapts automatically (and returns `0` when `< 4` active outlets exist).
- Among eligible declining outlets (`change_pct < 0`), take the `WEAK_OUTLET_COUNT` (5) steepest `%` declines (ties break on rupiah drop). Each outlet also tracks operational movement (`base_invoices -> current_invoices` and `base_skus -> current_skus`).

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

## 3. Telegram summary

Scannable multi-line message in Bahasa Indonesia (BLUF headline + bulleted KPIs + numbered `%` watch list + key-account Rupiah loss callout when distinct), generated from the report (never hard-coded). Built by `telegram_summary()`. The app only displays it with a copy button; it never sends anything.

Sample output:

```text
Ringkasan Penjualan Dua Kelinci — Sep–Okt 2026

Total penjualan bersih: Rp 1,73 miliar (naik 3,6%)
• Perbandingan: Sep Rp 847,5 jt → Okt Rp 878,4 jt
• Wilayah terbaik: Jabodetabek — Rp 495,8 jt (28,7% dari total)
• Merek terbaik: Kacang Dua Kelinci — Rp 739,8 jt (42,9% dari total)

Outlet perlu perhatian — penurunan % terdalam (Sep → Okt):
1. Minimarket Sido Muncul, Palembang (−69% · −Rp 6,3 jt)
2. Toko Bintang, Semarang (−63% · −Rp 5,5 jt)
3. Toko Anugerah, Palembang (−53% · −Rp 6,6 jt)
4. Toko Mekar, Banjarmasin (−52% · −Rp 2,7 jt)
5. Toko Sinar Abadi, Jakarta Barat (−48% · −Rp 3,4 jt)

Penurunan rupiah terbesar (akun besar):
• Grosir Sentosa, Bandung (−Rp 31,6 jt · −33%)
• Grosir Sumber Alam, Solo (−Rp 24,3 jt · −31%)
```

## Reference numbers (sample file)

| Figure | Value |
|---|---|
| Net sales total | Rp 1.725.966.000 |
| Sep / Okt | Rp 847.517.400 / Rp 878.448.600 (+3,6 %) |
| Best region | Jabodetabek Rp 495.827.800 (28,7 %) |
| Best brand | Kacang Dua Kelinci Rp 739.781.900 (42,9 %) |
| Outlets / invoices / cartons | 52 / 824 / 8.745 |

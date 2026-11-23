# Metrics

Implemented in `app/analysis.py`; thresholds in `app/config.py`; tested in `tests/test_analysis.py`.

## Shared definitions

- **Sales** always means `net_sales_idr` after cleaning (see [data.md](data.md)): after discount and net of returns.
- **Period**: every month present in the data. **Base** and **current** are the last two months (today: Sep 2026 → Okt 2026). With fewer than two months the app refuses to start.
- **Change %** = `(current − base) / base × 100`; undefined (shown as "baru") when base ≤ 0.

## 1. Sales per region and brand

For each region and each brand: sales per month, total, change %, and share of grand total. Sorted by total, highest first. The first row is the "best" region/brand used in the Telegram text.

## 2. Weakest outlets

**Rule:** the `WEAK_OUTLET_COUNT` (5) outlets with the largest **% decline** in sales from base to current month, among outlets whose base-month sales are at least `MIN_BASE_SALES_IDR` (Rp 5.000.000). Only declining outlets qualify, so fewer than 5 may be listed. Ties break on larger rupiah drop. An outlet with no current-month sales counts as −100 %.

**Why this rule** (the brief left "weakest" undefined):

- *Lowest total sales* only finds small outlets. The 5 lowest on the sample all sold < Rp 1,3 jt and 4 of them grew.
- *Largest rupiah drop* is dominated by big wholesalers that are still top outlets (Grosir Sentosa lost Rp 31,6 jt but is #2 by total).
- *% decline* finds outlets that are fading regardless of size, but tiny outlets produce noisy percentages (Rp 798 rb → 360 rb = −55 %). The Rp 5 jt floor (~60 % of the median outlet's September sales, Rp 8,0 jt) removes that noise.
- Outlets with no base-month sales are new, not weak, and are excluded.

The page also lists every outlet with its rupiah and % change, so large rupiah drops stay visible.

**Result on the sample data:**

| # | Outlet | Branch | Sep | Okt | Change |
|---|---|---|---|---|---|
| 1 | OUT1043 Minimarket Sido Muncul | Palembang | 9.181.700 | 2.873.700 | −68,7 % |
| 2 | OUT1022 Toko Bintang | Semarang | 8.764.300 | 3.223.100 | −63,2 % |
| 3 | OUT1041 Toko Anugerah | Palembang | 12.494.900 | 5.909.600 | −52,7 % |
| 4 | OUT1048 Toko Mekar | Banjarmasin | 5.143.700 | 2.473.900 | −51,9 % |
| 5 | OUT1001 Toko Sinar Abadi | Jakarta Barat | 6.929.900 | 3.579.000 | −48,4 % |

## 3. Telegram summary

One paragraph, Bahasa Indonesia, generated from the report (never hard-coded): total net sales, base → current with direction (naik/turun/stabil), best region and best brand with share, and the weakest outlets as `name branch (−N%)`. Built by `telegram_summary()`. The app only displays it with a copy button; it never sends anything.

Sample output:

> Ringkasan Penjualan Dua Kelinci Sep–Okt 2026: total penjualan bersih Rp 1,73 miliar (Sep Rp 847,5 jt → Okt Rp 878,4 jt, naik 3,6%). Wilayah terbaik Jabodetabek Rp 495,8 jt (28,7% dari total), merek terbaik Kacang Dua Kelinci Rp 739,8 jt (42,9%). Outlet yang perlu diperhatikan (penurunan terbesar Sep→Okt): Minimarket Sido Muncul Palembang (−69%), Toko Bintang Semarang (−63%), Toko Anugerah Palembang (−53%), Toko Mekar Banjarmasin (−52%), Toko Sinar Abadi Jakarta Barat (−48%).

## Reference numbers (sample file)

| Figure | Value |
|---|---|
| Net sales total | Rp 1.725.966.000 |
| Sep / Okt | Rp 847.517.400 / Rp 878.448.600 (+3,6 %) |
| Best region | Jabodetabek Rp 495.827.800 (28,7 %) |
| Best brand | Kacang Dua Kelinci Rp 739.781.900 (42,9 %) |
| Outlets / invoices / cartons | 52 / 824 / 8.745 |

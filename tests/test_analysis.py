"""Reference numbers below were verified by hand against the sample CSV.
If the data file changes, update them together with docs/metrics.md."""

import pytest

from app.analysis import adaptive_base_floor, change_pct, weakest_analysis, weakest_outlets
from app.formatting import date_id, pct, period_label, rp, rp_short


def test_totals(report):
    t = report["totals"]
    assert t["net"] == 1_725_966_000
    assert t["by_month"] == {"2026-09": 847_517_400, "2026-10": 878_448_600}
    assert t["change_pct"] == pytest.approx(3.65, abs=0.01)
    assert t["outlets"] == 52
    assert t["invoices"] == 824


def test_period(report):
    assert report["period"]["base"] == "2026-09"
    assert report["period"]["current"] == "2026-10"
    assert report["period"]["label"] == "Sep–Okt 2026"


def test_regions_ranked_and_complete(report):
    regions = report["regions"]
    assert [r["name"] for r in regions] == [
        "Jabodetabek", "Sumatera", "Jawa Barat", "Jawa Tengah", "Jawa Timur", "Kalimantan",
    ]
    assert regions[0]["total"] == 495_827_800
    assert [b["name"] for b in regions[0]["branches"]] == ["Tangerang", "Jakarta Barat", "Bekasi"]
    assert regions[0]["top_salesman"]["name"] == "Citra"
    assert sum(r["total"] for r in regions) == report["totals"]["net"]
    assert sum(r["share_pct"] for r in regions) == pytest.approx(100)


def test_branches_and_salesmen_ranked_and_complete(report):
    branches = report["branches"]
    assert len(branches) == 13
    assert branches[0]["name"] == "Tangerang"
    assert branches[0]["region"] == "Jabodetabek"
    assert branches[0]["total"] == 249_019_600
    assert branches[-1]["name"] == "Banjarmasin"
    assert sum(b["total"] for b in branches) == report["totals"]["net"]

    salesmen = report["salesmen"]
    named = report["named_salesmen"]
    assert len(named) == 26
    assert named[0]["name"] == "Citra"
    assert named[0]["branch"] == "Tangerang"
    assert named[0]["total"] == 136_587_300
    assert named[-1]["name"] == "Bayu"
    assert named[-1]["branch"] == "Banjarmasin"
    assert sum(s["total"] for s in salesmen) == report["totals"]["net"]

    ext = report["extremes"]
    assert ext["highest_outlet"]["outlet_id"] == "OUT1007"
    assert ext["lowest_outlet"]["outlet_id"] == "OUT1003"
    assert ext["steepest_drop_salesman"]["name"] == "Teguh"


def test_brands_ranked_and_complete(report):
    brands = report["brands"]
    assert brands[0]["name"] == "Kacang Dua Kelinci"
    assert brands[0]["total"] == 739_781_900
    assert len(brands) == 8
    assert sum(b["total"] for b in brands) == report["totals"]["net"]


def test_weakest_outlets(report):
    assert report["weakest_rule"]["min_base_idr"] == 4_927_700
    assert report["weakest_rule"]["q1_base_idr"] == 4_927_700
    assert report["weakest_rule"]["adaptive"] is True
    assert [o["outlet_id"] for o in report["weakest"]] == [
        "OUT1043", "OUT1022", "OUT1041", "OUT1048", "OUT1001",
    ]
    assert all(o["base"] >= report["weakest_rule"]["min_base_idr"] for o in report["weakest"])
    assert report["weakest"][0]["base_invoices"] == 5
    assert report["weakest"][0]["current_invoices"] == 3
    assert report["weakest"][0]["salesman"] == "Zaki, Yudi"
    assert "Zaki" in report["weakest"][0]["salesman_drop_note"]


def test_adaptive_base_floor_exact_unrounded():
    # N = 7 -> exclusive Q1 position = 0.25 * (7 + 1) = 2nd element = 483_250 (exact, not rounded to 500_000!)
    small_warungs = [{"base": b} for b in (400_000, 483_250, 490_000, 900_000, 1_100_000, 1_400_000, 1_800_000)]
    assert adaptive_base_floor(small_warungs) == 483_250

    # Fractional Q1 (N = 4 -> pos 1.25 -> 0.75 * 100 + 0.25 * 102 = 100.5):
    # Integer x >= 100.5 iff x >= 101 (math.ceil, not banker's round to 100).
    fractional_q1 = [{"base": b} for b in (100, 102, 200, 300)]
    assert adaptive_base_floor(fractional_q1) == 101

    tiny_count = [{"base": 1_000_000}, {"base": 2_000_000}]
    assert adaptive_base_floor(tiny_count) == 0


def test_funnel_partition_and_return_invoice_edges(report):
    # When min_base_idr == 0 (< 4 active outlets) AND a new outlet (base == 0) exists,
    # new + small + eligible must still partition total without double-counting.
    tiny_outlets = [
        {"outlet_id": "NEW1", "base": 0, "current": 5_000_000, "total": 5_000_000, "change_idr": 5_000_000, "change_pct": None, "eb_change_pct": None},
        {"outlet_id": "ACT1", "base": 4_000_000, "current": 2_000_000, "total": 6_000_000, "change_idr": -2_000_000, "change_pct": -50.0, "eb_change_pct": -30.0},
        {"outlet_id": "ACT2", "base": 6_000_000, "current": 7_000_000, "total": 13_000_000, "change_idr": 1_000_000, "change_pct": 16.7, "eb_change_pct": 10.0},
    ]
    floor = adaptive_base_floor(tiny_outlets)
    assert floor == 0
    wa = weakest_analysis(tiny_outlets, floor, 5)
    assert len(wa["new"]) == 1
    assert len(wa["small"]) == 0
    assert wa["eligible"] == 2
    assert len(wa["new"]) + len(wa["small"]) + wa["eligible"] == wa["total"]

    # Return credit note RTR900001 on OUT1049 must not inflate positive sales invoice count.
    out1049 = next(o for o in report["outlets"] if o["outlet_id"] == "OUT1049")
    assert out1049["current_invoices"] == 8


def test_weakest_analysis_funnel(report):
    a = report["weakest_analysis"]
    assert a["total"] == 52
    assert [o["outlet_id"] for o in a["new"]] == ["OUT1047"]
    assert len(a["small"]) == 12
    assert a["eligible"] == 39
    assert a["total"] - len(a["new"]) - len(a["small"]) == a["eligible"]
    assert a["declining"] == 21
    assert [o["outlet_id"] for o in a["lowest_total"]][:2] == ["OUT1003", "OUT1026"]
    assert [o["outlet_id"] for o in a["largest_drop_idr"]][:2] == ["OUT1014", "OUT1025"]
    assert [o["outlet_id"] for o in a["revenue_at_risk"]][:2] == ["OUT1014", "OUT1025"]
    assert a["risk_drop_share_pct"] == pytest.approx(68.5, abs=0.2)
    eb_ids = [o["outlet_id"] for o in a["empirical_bayes"]]
    assert "OUT1043" in eb_ids and "OUT1014" in eb_ids


def test_weakest_rule_edges():
    outlets = [
        {"outlet_id": "tiny", "base": 800_000, "current": 100_000, "change_idr": -700_000, "change_pct": -87.5},
        {"outlet_id": "new", "base": 0, "current": 9_000_000, "change_idr": 9_000_000, "change_pct": None},
        {"outlet_id": "grew", "base": 9_000_000, "current": 9_500_000, "change_idr": 500_000, "change_pct": 5.6},
        {"outlet_id": "gone", "base": 6_000_000, "current": 0, "change_idr": -6_000_000, "change_pct": -100.0},
        {"outlet_id": "dip", "base": 50_000_000, "current": 45_000_000, "change_idr": -5_000_000, "change_pct": -10.0},
    ]
    assert [o["outlet_id"] for o in weakest_outlets(outlets, 5_000_000, 5)] == ["gone", "dip"]


def test_change_pct_without_base():
    assert change_pct(0, 100) is None
    assert change_pct(200, 100) == -50


def test_telegram_summary(report):
    text = report["telegram_summary"]
    assert text.count("\n") >= 20
    assert len(text) < 4096  # fits inside a single Telegram message
    for expected in (
        "Ringkasan Penjualan Dua Kelinci — Sep–Okt 2026",
        "Total penjualan bersih: Rp 1,73 miliar (naik 3,6%)",
        "Sep Rp 847,5 jt → Okt Rp 878,4 jt",
        "Wilayah terbaik: Jabodetabek — Rp 495,8 jt (28,7% dari total)",
        "Cabang kota: Tangerang Rp 249,0 jt · Jakarta Barat Rp 168,8 jt · Bekasi Rp 78,0 jt",
        "Cabang tertinggi: Tangerang (Jabodetabek) — Rp 249,0 jt",
        "Merek terbaik: Kacang Dua Kelinci — Rp 739,8 jt (42,9% dari total)",
        "Salesman tertinggi: Citra (Tangerang, Jabodetabek) — Rp 136,6 jt",
        "Outlet tertinggi: [OUT1007] Grosir Harapan Baru, Tangerang",
        "Outlet terendah: [OUT1003] Toko Sinar Abadi, Jakarta Barat",
        "Wilayah & cabang terendah: Kalimantan (Rp 144,2 jt) · Banjarmasin (Rp 32,0 jt)",
        "Merek & salesman terendah: Roni (Rp 34,4 jt) · Bayu, Banjarmasin (Rp 13,1 jt)",
        "1. [OUT1043] Minimarket Sido Muncul, Palembang (Sumatera)",
        "Sales: Zaki, Yudi — drop utama Zaki",
        "5. [OUT1001] Toko Sinar Abadi, Jakarta Barat (Jabodetabek)",
        "[OUT1014] Grosir Sentosa, Bandung (Jawa Barat): −Rp 31,6 jt",
        "drop utama Gita",
    ):
        assert expected in text


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1_725_966_000, "Rp 1,73 miliar"), (495_827_800, "Rp 495,8 jt"), (528_000, "Rp 528 rb"),
     (-528_000, "−Rp 528 rb"), (950, "Rp 950")],
)
def test_rp_short(value, expected):
    assert rp_short(value) == expected


def test_rp_and_pct():
    assert rp(1_725_966_000) == "Rp 1.725.966.000"
    assert rp(-528_000) == "−Rp 528.000"
    assert pct(3.6496) == "+3,6%"
    assert pct(-68.7, digits=0) == "−69%"
    assert pct(28.7, signed=False) == "28,7%"
    assert pct(None) == "baru"


def test_period_label_across_years():
    assert period_label(["2026-12", "2027-01"]) == "Des 2026–Jan 2027"
    assert date_id("2026-10-31") == "31 Okt 2026"


def test_outlet_sku_diagnostics(report):
    by_id = {o["outlet_id"]: o for o in report["outlets"]}

    # Every outlet's SKU deltas sum identically to the outlet's net Rupiah delta
    for o in report["outlets"]:
        assert sum(s["change_idr"] for s in o["skus"]) == o["change_idr"]
        sk = o["sku_summary"]
        assert sk["total"] == len(o["skus"]) == sk["stopped"] + sk["running"]
        assert sk["running"] == sk["retained"] + sk["new"]

    sido = by_id["OUT1043"]
    assert sido["sku_summary"] == {
        "total": 9,
        "stopped": 4,
        "stopped_idr": -3_397_200,
        "running": 5,
        "retained": 5,
        "declining": 4,
        "growing": 1,
        "new": 0,
    }
    assert sido["skus"][0]["sku"] == "Tic Tac Original 80g"
    assert sido["skus"][0]["status"] == "berhenti"
    assert sido["skus"][0]["base_cartons"] == 6 and sido["skus"][0]["current_cartons"] == 0
    assert any(s["sku"] == "Usagi Wheat Puffs 45g" and s["status"] == "tumbuh" for s in sido["skus"])
    assert sido["last_order_date"] == "2026-10-31"
    assert sido["last_order_salesman"] == "Yudi"

    anugerah = by_id["OUT1041"]
    assert anugerah["sku_summary"]["stopped"] == 5
    assert anugerah["sku_summary"]["new"] == 3
    assert anugerah["sku_summary"]["running"] == 8

    sentosa = by_id["OUT1014"]
    assert sentosa["sku_summary"]["stopped"] == 0
    assert sentosa["sku_summary"]["running"] == 13
    assert sentosa["sku_summary"]["declining"] == 9

"""Reference numbers below were verified by hand against the sample CSV.
If the data file changes, update them together with docs/metrics.md."""

import pytest

from app.analysis import change_pct, weakest_outlets
from app.formatting import pct, period_label, rp, rp_short


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
    assert sum(r["total"] for r in regions) == report["totals"]["net"]
    assert sum(r["share_pct"] for r in regions) == pytest.approx(100)


def test_brands_ranked_and_complete(report):
    brands = report["brands"]
    assert brands[0]["name"] == "Kacang Dua Kelinci"
    assert brands[0]["total"] == 739_781_900
    assert len(brands) == 8
    assert sum(b["total"] for b in brands) == report["totals"]["net"]


def test_weakest_outlets(report):
    assert [o["outlet_id"] for o in report["weakest"]] == [
        "OUT1043", "OUT1022", "OUT1041", "OUT1048", "OUT1001",
    ]
    assert all(o["base"] >= report["weakest_rule"]["min_base_idr"] for o in report["weakest"])


def test_weakest_analysis_funnel(report):
    a = report["weakest_analysis"]
    assert a["total"] == 52
    assert [o["outlet_id"] for o in a["new"]] == ["OUT1047"]
    assert len(a["small"]) == 13
    assert a["eligible"] == 38
    assert a["total"] - len(a["new"]) - len(a["small"]) == a["eligible"]
    assert a["declining"] == 21
    assert [o["outlet_id"] for o in a["lowest_total"]][:2] == ["OUT1003", "OUT1026"]
    assert [o["outlet_id"] for o in a["largest_drop_idr"]][:2] == ["OUT1014", "OUT1025"]


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
    assert text.count("\n") >= 10
    for expected in (
        "Ringkasan Penjualan Dua Kelinci — Sep–Okt 2026",
        "Total penjualan bersih: Rp 1,73 miliar (naik 3,6%)",
        "Sep Rp 847,5 jt → Okt Rp 878,4 jt",
        "Jabodetabek — Rp 495,8 jt (28,7% dari total)",
        "Kacang Dua Kelinci — Rp 739,8 jt (42,9% dari total)",
        "1. Minimarket Sido Muncul, Palembang (−69% · −Rp 6,3 jt)",
        "5. Toko Sinar Abadi, Jakarta Barat (−48% · −Rp 3,4 jt)",
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

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # `with` runs the lifespan, which loads the CSV
        yield c


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_inter_font_is_self_hosted(client):
    for font in ("InterVariable.woff2", "MontserratVariable.woff2"):
        res = client.get(f"/static/fonts/{font}")
        assert res.status_code == 200
        assert "font/woff2" in res.headers["content-type"]
        assert res.content[:4] == b"wOF2"
    for lic in ("LICENSE-Inter.txt", "LICENSE-Montserrat.txt"):
        lic_res = client.get(f"/static/fonts/{lic}")
        assert lic_res.status_code == 200
        assert len(lic_res.content) > 1000
    res = client.get("/static/logo-dk.png")
    assert res.status_code == 200
    assert "image/png" in res.headers["content-type"]
    assert res.content[:8] == b"\x89PNG\r\n\x1a\n"
    ico = client.get("/favicon.ico")
    assert ico.status_code == 200
    assert "image/x-icon" in ico.headers["content-type"]
    assert ico.content[:4] == b"\x00\x00\x01\x00"
    for fav in ("favicon.png", "apple-touch-icon.png"):
        f_res = client.get(f"/static/{fav}")
        assert f_res.status_code == 200
        assert "image/png" in f_res.headers["content-type"]
        assert f_res.content[:8] == b"\x89PNG\r\n\x1a\n"
    css_res = client.get("/static/app.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]
    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers["content-type"]
    home = client.get("/").text
    assert 'rel="icon"' in home
    assert "favicon.png" in home
    assert "/static/fonts/InterVariable.woff2" in home
    assert "/static/fonts/MontserratVariable.woff2" in home
    assert "fonts.googleapis.com" not in home
    assert "https://duakelinci.com" not in home


def test_report_json(client):
    res = client.get("/api/report")
    assert res.status_code == 200
    body = res.json()
    assert body["totals"]["net"] == 1_725_966_000
    assert len(body["weakest"]) == 5
    assert body["telegram_summary"].startswith("Penjualan bersih Oktober 2026 **Rp878,4 juta**")
    assert "\n" not in body["telegram_summary"]


def page(client, path: str) -> str:
    res = client.get(path)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/html")
    return res.text


def test_ringkasan_page(client):
    html = page(client, "/")
    for expected in (
        "Ringkasan penjualan",
        "Ringkasan untuk Telegram",
        'data-copy="tg"',
        "Semua outlet",
        'id="outlet-search"',
        'id="f-branch"',
        'id="f-salesman"',
        'aria-sort="ascending"',  # outlet table starts sorted by % change
        'role="region"',  # scrolling tables are keyboard-focusable regions
        'id="sidebar"',
        "data-sidebar-toggle",
        'id="upload-dialog"',
        "data-open-upload",
        'aria-current="page"',
        "Jabodetabek",
        "Tangerang",
        "Citra",
        "Kacang Dua Kelinci",
        "Minimarket Sido Muncul",
        "OUT1007",
        "OUT1003",
    ):
        assert expected in html
    assert 'href="/wilayah-merek"' in html and 'href="/outlet-terlemah"' in html
    assert 'class="stat-strip"' in html
    assert "pill pill-pos" in html and "pill pill-neg" in html


def test_wilayah_merek_page_switches_view(client):
    html = page(client, "/wilayah-merek")
    assert "Rincian penjualan" in html
    assert "tabbed-sheet" in html
    assert "numbered-table" in html
    assert "data-dim-nav" in html
    assert 'data-dim-tab="wilayah" aria-current="page"' in html
    assert 'id="search-wilayah"' in html
    assert 'id="search-salesman"' in html
    assert 'data-view="wilayah" aria-labelledby="h-wilayah">' in html  # visible
    assert 'data-view="merek" aria-labelledby="h-merek" hidden' in html
    assert 'data-view="salesman" aria-labelledby="h-salesman" hidden' in html
    html = page(client, "/wilayah-merek?lihat=merek")
    assert 'data-dim-tab="merek" aria-current="page"' in html
    assert 'data-view="wilayah" aria-labelledby="h-wilayah" hidden' in html
    assert 'data-view="merek" aria-labelledby="h-merek">' in html
    assert "Rp 739.781.900" in html  # Kacang Dua Kelinci total, full rupiah
    html = page(client, "/wilayah-merek?lihat=salesman")
    assert 'data-dim-tab="salesman" aria-current="page"' in html
    assert 'data-view="salesman" aria-labelledby="h-salesman">' in html
    assert "Rp 136.587.300" in html  # Citra total, full rupiah
    html = page(client, "/wilayah-merek?lihat=cabang")
    assert 'data-dim-tab="cabang" aria-current="page"' in html
    assert 'data-view="cabang" aria-labelledby="h-cabang">' in html
    assert "Rp 249.019.600" in html  # Tangerang total, full rupiah
    html = page(client, "/wilayah-merek?lihat=anything")  # unknown value falls back
    assert 'data-view="wilayah" aria-labelledby="h-wilayah">' in html


def test_outlet_terlemah_page_shows_calculation(client):
    html = page(client, "/outlet-terlemah")
    for expected in (
        "Hasil dan hitungannya",
        'id="weakest-table"',
        'id="risk-table"',
        'id="weak-search"',
        "data-lens-switch",
        "Cabang",
        "Salesman",
        "Aksi",
        'data-peek-open="OUT1043"',
        'data-peek-open="OUT1014"',
        'id="outlet-side-peek"',
        "data-peek-close",
        "data-peek-prev",
        "data-peek-next",
        "data-peek-copy",
        "Frekuensi Faktur",
        "Volume Karton",
        "Variasi Produk",
        "Order Terakhir",
        "Status &amp; Pergerakan SKU",
        'data-sku-filter="berhenti"',
        'data-sku-filter="jalan"',
        "Tic Tac Original 80g",
        "Usagi Wheat Puffs 45g",
        "Atribusi Penurunan per Salesman",
        "Pemicu utama drop",
        "Zaki, Yudi",
        "Palembang",
        "Aturan yang dipakai",
        "Rp 4.927.700",
        "Cara menyaring 52 outlet",
        "Keluarkan 1 outlet baru",
        "Keluarkan 12 outlet kecil",
        "−Rp 6.308.000 ÷ Rp 9.181.700 × 100",
        "−68,7%",
    ):
        assert expected in html
    assert "Kenapa tidak memakai cara lain?" not in html
    assert html.index('id="weakest-table"') < html.index("Aturan yang dipakai")


def test_unknown_page_is_404(client):
    assert client.get("/tidak-ada").status_code == 404


def test_sample_csv_download(client):
    res = client.get("/api/sample-csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "dua_kelinci_sample_sales_sep_oct_2026.csv" in res.headers.get("content-disposition", "")
    assert res.text.startswith("date,invoice_no,region,branch,outlet_id,")


def test_upload_csv_and_reset_flow(client):
    custom_csv = (
        "date,invoice_no,region,branch,outlet_id,outlet_name,outlet_type,salesman,brand,sku,"
        "qty_carton,price_per_carton_idr,gross_sales_idr,discount_idr,net_sales_idr\n"
        "2026-11-05,INV1,Jabodetabek,Jakarta Barat,OUT1,Grosir Jaya,Grosir,Budi,Sukro,Sukro 100g,50,200000,10000000,0,10000000\n"
        "2026-12-06,INV2,Jabodetabek,Jakarta Barat,OUT1,Grosir Jaya,Grosir,Budi,Sukro,Sukro 100g,25,200000,5000000,0,5000000\n"
        "2026-11-10,INV3,Jabar,Bandung,OUT2,Toko Makmur,Toko Kelontong,Siti,Tic Tac,Tic Tac 90g,30,200000,6000000,0,6000000\n"
        "2026-12-12,INV4,Jawa Barat,Bandung,OUT2,Toko Makmur,Toko Kelontong,Siti,Tic Tac,Tic Tac 90g,45,200000,9000000,0,9000000\n"
    ).encode("utf-8")

    try:
        res = client.post(
            "/api/upload",
            files={"file": ("../penjualan_nov_des_2026.csv", custom_csv, "text/csv")},
            headers={"Accept": "application/json"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body == {
            "ok": True,
            "source": "penjualan_nov_des_2026.csv",
            "period": "Nov–Des 2026",
            "clean_rows": 4,
            "outlets": 2,
        }

        rep = client.get("/api/report").json()
        assert rep["source"] == "penjualan_nov_des_2026.csv"
        assert rep["totals"]["net"] == 30_000_000
        assert len(rep["weakest"]) == 1
        assert rep["weakest"][0]["name"] == "Grosir Jaya"

        for path in ("/", "/wilayah-merek", "/outlet-terlemah"):
            rendered = page(client, path)
            assert "penjualan_nov_des_2026.csv" in rendered
            assert "Kustom" in rendered
    finally:
        reset_res = client.post("/api/report/reset", headers={"Accept": "application/json"})
        assert reset_res.status_code == 200
        assert reset_res.json()["ok"] is True

    restored = client.get("/api/report").json()
    assert restored["totals"]["net"] == 1_725_966_000


def test_custom_csv_has_zero_hardcoded_sample_leakage(client):
    """Uploading a CSV with completely new months, regions, branches, salesmen, outlets, and SKUs
    must render 100% real values from that CSV with zero leftover strings from the sample dataset."""
    custom_csv = (
        "date,invoice_no,region,branch,outlet_id,outlet_name,outlet_type,salesman,brand,sku,"
        "qty_carton,price_per_carton_idr,gross_sales_idr,discount_idr,net_sales_idr\n"
        "2026-12-04,INV-A1,Sulawesi,Makassar,CUST-901,Pasar Segar Panakkukang,Grosir,Daeng,Mix Nut,Mix Nut Spesial 150g,40,250000,10000000,0,10000000\n"
        "2026-12-12,INV-A2,Sulawesi,Makassar,CUST-901,Pasar Segar Panakkukang,Grosir,Daeng,Kacang Polong,Polong Pedas 80g,20,200000,4000000,0,4000000\n"
        "2027-01-08,INV-A3,Sulawesi,Makassar,CUST-901,Pasar Segar Panakkukang,Grosir,Daeng,Mix Nut,Mix Nut Spesial 150g,15,250000,3750000,0,3750000\n"
        "2026-12-06,INV-B1,Bali Nusra,Denpasar,CUST-902,Minimarket Dewata,Minimarket,Putu,Kacang Polong,Polong Hijau 80g,30,200000,6000000,0,6000000\n"
        "2027-01-14,INV-B2,Bali Nusra,Denpasar,CUST-902,Minimarket Dewata,Minimarket,Putu,Kacang Polong,Polong Hijau 80g,45,200000,9000000,0,9000000\n"
        "2026-12-09,INV-C1,Bali Nusra,Denpasar,CUST-903,Grosir Pantai Kuta,Grosir,Putu,Mix Nut,Mix Nut Spesial 150g,32,250000,8000000,0,8000000\n"
        "2027-01-18,INV-C2,Bali Nusra,Denpasar,CUST-903,Grosir Pantai Kuta,Grosir,Putu,Mix Nut,Mix Nut Spesial 150g,40,250000,10000000,0,10000000\n"
        "2026-12-11,INV-D1,Sulawesi,Makassar,CUST-904,Warung Anging Mammiri,Warung,Daeng,Kacang Polong,Polong Hijau 80g,10,200000,2000000,0,2000000\n"
        "2027-01-21,INV-D2,Sulawesi,Makassar,CUST-904,Warung Anging Mammiri,Warung,Daeng,Kacang Polong,Polong Hijau 80g,12,200000,2400000,0,2400000\n"
    ).encode("utf-8")

    forbidden_sample_terms = (
        "Jabodetabek",
        "Jawa Barat",
        "Sumatera",
        "Palembang",
        "Tangerang",
        "Bandung",
        "Citra",
        "Zaki",
        "Yudi",
        "OUT1043",
        "OUT1007",
        "Minimarket Sido Muncul",
        "Kacang Dua Kelinci",
        "Tic Tac Original 80g",
        "1.725.966.000",
        "4.927.700",
        "Sep–Okt",
    )

    try:
        res = client.post(
            "/api/upload",
            files={"file": ("penjualan_indonesia_timur.csv", custom_csv, "text/csv")},
            headers={"Accept": "application/json"},
        )
        assert res.status_code == 200

        home = page(client, "/")
        rincian = page(client, "/wilayah-merek?lihat=salesman")
        weak = page(client, "/outlet-terlemah")

        for expected_home in (
            "Des 2026–Jan 2027",
            "Bali Nusra",
            "Sulawesi",
            "Denpasar",
            "Makassar",
            "Putu",
            "Daeng",
            "1 Prioritas Tindak Lanjut",
            "CUST-901",
            "Pasar Segar Panakkukang",
        ):
            assert expected_home in home

        for expected_rincian in ("Putu", "Daeng", "Denpasar", "Makassar", "Rp 55.150.000"):
            assert expected_rincian in rincian

        for expected_weak in (
            "Des 2026 → Jan 2027",
            'data-peek-open="CUST-901"',
            "Pasar Segar Panakkukang",
            "Polong Pedas 80g",       # stopped SKU in CUST-901
            "Mix Nut Spesial 150g",   # still-running SKU in CUST-901
            "21 Jan 2027",            # or 8 Jan 2027 on CUST-901
        )[:5]:
            assert expected_weak in weak
        assert "8 Jan 2027" in weak  # real last_order_date of CUST-901 from CSV

        for html_doc in (home, rincian, weak):
            for forbidden in forbidden_sample_terms:
                assert forbidden not in html_doc
    finally:
        reset_res = client.post("/api/report/reset", headers={"Accept": "application/json"})
        assert reset_res.status_code == 200


def test_upload_csv_validation_errors_preserve_active_report(client):
    missing_cols = b"date,region\n2026-09-01,Jabar\n"
    r1 = client.post(
        "/api/upload",
        files={"file": ("kurang.csv", missing_cols, "text/csv")},
        headers={"Accept": "application/json"},
    )
    assert r1.status_code == 400
    assert "Kolom wajib belum lengkap" in r1.json()["detail"]

    one_month = (
        "date,invoice_no,region,branch,outlet_id,outlet_name,outlet_type,salesman,brand,sku,"
        "qty_carton,price_per_carton_idr,gross_sales_idr,discount_idr,net_sales_idr\n"
        "2026-09-05,INV1,Jabodetabek,Jakarta,OUT1,Toko A,Warung,Budi,Sukro,S,10,100000,1000000,0,1000000\n"
    ).encode("utf-8")
    r2 = client.post(
        "/api/upload",
        files={"file": ("satu_bulan.csv", one_month, "text/csv")},
        headers={"Accept": "application/json"},
    )
    assert r2.status_code == 400
    assert "minimal 2 bulan" in r2.json()["detail"]

    fake_xlsx = b"PK\x03\x04fake-excel-archive"
    r3 = client.post(
        "/api/upload",
        files={"file": ("laporan.xlsx", fake_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Accept": "application/json"},
    )
    assert r3.status_code == 400
    assert "Excel" in r3.json()["detail"]

    assert client.get("/api/report").json()["totals"]["net"] == 1_725_966_000

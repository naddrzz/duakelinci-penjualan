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
        assert res.content[:4] == b"wOF2"
    res = client.get("/static/logo-dk.png")
    assert res.status_code == 200
    assert res.content[:8] == b"\x89PNG\r\n\x1a\n"
    home = client.get("/").text
    assert "fonts.googleapis.com" not in home
    assert "https://duakelinci.com" not in home


def test_report_json(client):
    res = client.get("/api/report")
    assert res.status_code == 200
    body = res.json()
    assert body["totals"]["net"] == 1_725_966_000
    assert len(body["weakest"]) == 5
    assert body["telegram_summary"].startswith("Ringkasan Penjualan Dua Kelinci")


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
        'aria-sort="ascending"',  # outlet table starts sorted by % change
        'role="region"',  # scrolling tables are keyboard-focusable regions
        'id="sidebar"',
        "data-sidebar-toggle",
        'id="upload-dialog"',
        "data-open-upload",
        'aria-current="page"',
        "Jabodetabek",
        "Kacang Dua Kelinci",
        "Minimarket Sido Muncul",
    ):
        assert expected in html
    assert 'href="/wilayah-merek"' in html and 'href="/outlet-terlemah"' in html
    assert "bar bar-pos" in html and "bar bar-neg" in html


def test_wilayah_merek_page_switches_view(client):
    html = page(client, "/wilayah-merek")
    assert 'id="lihat"' in html
    assert 'data-view="wilayah" aria-labelledby="h-wilayah">' in html  # visible
    assert 'data-view="merek" aria-labelledby="h-merek" hidden' in html
    html = page(client, "/wilayah-merek?lihat=merek")
    assert 'data-view="wilayah" aria-labelledby="h-wilayah" hidden' in html
    assert 'data-view="merek" aria-labelledby="h-merek">' in html
    assert html.index("Tabel penjualan per merek") < html.rindex('class="view-switch"')
    assert "Rp 739.781.900" in html  # Kacang Dua Kelinci total, full rupiah
    html = page(client, "/wilayah-merek?lihat=anything")  # unknown value falls back
    assert 'data-view="wilayah" aria-labelledby="h-wilayah">' in html


def test_outlet_terlemah_page_shows_calculation(client):
    html = page(client, "/outlet-terlemah")
    for expected in (
        "Hasil dan hitungannya",
        'id="weakest-table"',
        "Aturan yang dipakai",
        "Cara menyaring 52 outlet",
        "Keluarkan 1 outlet baru",
        "Keluarkan 13 outlet kecil",
        "−Rp 6.308.000 ÷ Rp 9.181.700 × 100",  # Minimarket Sido Muncul
        "−68,7%",
        "Kenapa tidak memakai cara lain?",
    ):
        assert expected in html
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

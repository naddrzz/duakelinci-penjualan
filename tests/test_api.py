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
    assert "Rp 739.781.900" in html  # Kacang Dua Kelinci total, full rupiah
    html = page(client, "/wilayah-merek?lihat=anything")  # unknown value falls back
    assert 'data-view="wilayah" aria-labelledby="h-wilayah">' in html


def test_outlet_terlemah_page_shows_calculation(client):
    html = page(client, "/outlet-terlemah")
    for expected in (
        "Aturan yang dipakai",
        "Cara menyaring 52 outlet",
        "Keluarkan 1 outlet baru",
        "Keluarkan 13 outlet kecil",
        "Hasil dan hitungannya",
        "−Rp 6.308.000 ÷ Rp 9.181.700 × 100",  # Minimarket Sido Muncul
        "−68,7%",
        "Kenapa tidak memakai cara lain?",
    ):
        assert expected in html


def test_unknown_page_is_404(client):
    assert client.get("/tidak-ada").status_code == 404

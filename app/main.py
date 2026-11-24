"""FastAPI entry point. The default CSV is loaded once at startup; users may also upload a custom CSV."""

import mimetypes
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from email.parser import BytesParser
from email.policy import HTTP
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .analysis import build_report
from .data import REQUIRED_COLUMNS, load_sales, load_sales_text
from .formatting import date_id, month_label, month_short, pct, rp, rp_short, rp_tg, tg_preview_html

# Guarantee deterministic MIME headers even in minimal slim containers without /etc/mime.types.
for _mime, _ext in (
    ("font/woff2", ".woff2"),
    ("image/x-icon", ".ico"),
    ("image/png", ".png"),
    ("image/svg+xml", ".svg"),
    ("text/css", ".css"),
    ("text/javascript", ".js"),
    ("text/plain", ".txt"),
):
    mimetypes.add_type(_mime, _ext)

STATIC_DIR = Path(__file__).parent / "static"
SAFE_PATHS = {"/", "/wilayah-merek", "/outlet-terlemah"}

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters.update(
    rp=rp,
    rp_short=rp_short,
    rp_tg=rp_tg,
    tg_preview=tg_preview_html,
    pct=pct,
    month_label=month_label,
    month_short=month_short,
    date_id=date_id,
)
templates.env.globals["required_columns"] = REQUIRED_COLUMNS


class _UploadError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def asset_url(name: str) -> str:
    """URL of a static file with its modification time as a cache-busting version."""
    return f"/static/{name}?v={int((STATIC_DIR / name).stat().st_mtime)}"


templates.env.globals["asset_url"] = asset_url


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    rows, cleaning = load_sales(config.DATA_PATH)
    default_report = build_report(
        rows,
        cleaning,
        source=config.DATA_PATH.name,
        min_base_idr=None,
        weak_count=config.WEAK_OUTLET_COUNT,
    )
    app.state.default_report = default_report
    app.state.report = default_report
    yield


app = FastAPI(title="Dua Kelinci Sales Summary", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "application/json" in accept


def _safe_referer(request: Request) -> str:
    ref = request.headers.get("referer", "")
    if ref:
        parts = urlsplit(ref)
        if parts.path in SAFE_PATHS:
            if parts.path == "/wilayah-merek" and parts.query in (
                "lihat=wilayah",
                "lihat=cabang",
                "lihat=merek",
                "lihat=salesman",
            ):
                return f"{parts.path}?{parts.query}"
            return parts.path
    return "/"


def _sanitize_filename(raw_name: str) -> str:
    base = Path(raw_name.replace("\\", "/")).name
    cleaned = "".join(ch for ch in base if ch.isprintable()).strip()[:80]
    return cleaned or "upload.csv"


async def _read_limited_body(request: Request, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > max_bytes:
            raise _UploadError(413, "Ukuran berkas melebihi batas maksimum 10 MB.")
        chunks.append(chunk)
    return b"".join(chunks)


def _extract_csv_upload(request: Request, raw_body: bytes) -> tuple[str, bytes]:
    content_type = request.headers.get("content-type", "")
    lower_ct = content_type.lower()
    if lower_ct.startswith("multipart/form-data"):
        if not raw_body:
            raise _UploadError(400, "Pilih berkas CSV terlebih dahulu.")
        raw_msg = b"Content-Type: " + content_type.encode("latin-1", errors="ignore") + b"\r\n\r\n" + raw_body
        msg = BytesParser(policy=HTTP).parsebytes(raw_msg)
        if msg.is_multipart():
            for part in msg.iter_parts():
                if part.get_param("name", header="content-disposition") == "file":
                    filename = part.get_filename() or "upload.csv"
                    payload = part.get_payload(decode=True) or b""
                    return filename, payload
        raise _UploadError(400, "Berkas CSV tidak ditemukan pada formulir unggah.")
    if lower_ct.startswith(("text/csv", "application/csv")):
        return request.headers.get("x-filename", "upload.csv"), raw_body
    raise _UploadError(400, "Format permintaan tidak didukung. Unggah berkas dengan format .csv.")


def _friendly_validation_error(err: ValueError) -> str:
    msg = str(err)
    if "missing columns [" in msg:
        match = re.search(r"missing columns \[(.*)\]", msg)
        cols = match.group(1).replace("'", "") if match else msg
        return f"Kolom wajib belum lengkap ({cols}). Gunakan struktur 15 kolom sesuai contoh CSV."
    if msg.startswith("line "):
        line_no = msg.split(":", 1)[0].replace("line ", "")
        return (
            f"Data pada baris {line_no} tidak valid. Pastikan kolom date berformat YYYY-MM-DD "
            f"dan kolom kuantitas serta rupiah berupa bilangan bulat."
        )
    if "need at least two months" in msg:
        return "Data harus memuat minimal 2 bulan transaksi (mis. 2026-09 dan 2026-10) agar perbandingan antarbulan dapat dihitung."
    return f"Berkas CSV tidak valid: {msg}"


def render(request: Request, template: str, page: str, title: str, **extra: object) -> HTMLResponse:
    is_custom = request.app.state.report is not request.app.state.default_report
    context = {
        "r": request.app.state.report,
        "is_custom_data": is_custom,
        "default_source": config.DATA_PATH.name,
        "page": page,
        "title": title,
        **extra,
    }
    return templates.TemplateResponse(request, template, context)


@app.get("/", response_class=HTMLResponse)
def ringkasan(request: Request) -> HTMLResponse:
    return render(request, "ringkasan.html", "ringkasan", "Ringkasan")


@app.get("/wilayah-merek", response_class=HTMLResponse)
def wilayah_merek(request: Request, lihat: str = "wilayah") -> HTMLResponse:
    view = lihat if lihat in ("wilayah", "cabang", "merek", "salesman") else "wilayah"
    return render(request, "wilayah_merek.html", "wilayah-merek", "Rincian penjualan", view=view)


@app.get("/outlet-terlemah", response_class=HTMLResponse)
def outlet_terlemah(request: Request) -> HTMLResponse:
    return render(request, "outlet_terlemah.html", "outlet-terlemah", "Outlet terlemah")


@app.get("/api/report")
def api_report(request: Request) -> dict:
    return request.app.state.report


@app.get("/api/sample-csv")
def sample_csv() -> FileResponse:
    return FileResponse(
        config.DATA_PATH,
        media_type="text/csv; charset=utf-8",
        filename=config.DATA_PATH.name,
    )


@app.post("/api/upload")
async def upload_csv(request: Request) -> Response:
    try:
        raw_body = await _read_limited_body(request, config.MAX_UPLOAD_BYTES)
        raw_name, payload = _extract_csv_upload(request, raw_body)
        safe_name = _sanitize_filename(raw_name)

        if safe_name.lower().endswith((".xlsx", ".xls")) or payload.startswith((b"PK\x03\x04", b"\xd0\xcf\x11\xe0")):
            raise _UploadError(
                400,
                "Berkas Excel (.xlsx/.xls) tidak didukung langsung. Simpan terlebih dahulu sebagai CSV UTF-8 (.csv).",
            )
        if not payload.strip():
            raise _UploadError(400, "Berkas CSV kosong. Pilih berkas yang berisi baris transaksi.")

        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise _UploadError(
                400,
                "Berkas tidak dapat dibaca sebagai UTF-8. Simpan ulang berkas dalam format CSV UTF-8.",
            ) from exc

        try:
            rows, cleaning = load_sales_text(text, source_name=safe_name)
            if not rows:
                raise _UploadError(400, "Berkas CSV tidak memiliki baris transaksi.")
            new_report = build_report(
                rows,
                cleaning,
                source=safe_name,
                min_base_idr=None,
                weak_count=config.WEAK_OUTLET_COUNT,
            )
        except ValueError as exc:
            raise _UploadError(400, _friendly_validation_error(exc)) from exc

        request.app.state.report = new_report
    except _UploadError as err:
        if _wants_json(request):
            return JSONResponse({"ok": False, "detail": err.message}, status_code=err.status)
        return HTMLResponse(
            f'<!doctype html><html lang="id"><meta charset="utf-8"><title>Gagal mengunggah CSV</title>'
            f'<body style="font-family:system-ui,sans-serif;max-width:560px;margin:48px auto;padding:0 16px;line-height:1.5">'
            f"<h1>Gagal memuat CSV</h1><p>{err.message}</p>"
            f'<p><a href="{_safe_referer(request)}">&larr; Kembali ke dasbor</a></p></body></html>',
            status_code=err.status,
        )

    if _wants_json(request):
        return JSONResponse({
            "ok": True,
            "source": new_report["source"],
            "period": new_report["period"]["label"],
            "clean_rows": new_report["data_quality"]["clean_rows"],
            "outlets": new_report["totals"]["outlets"],
        })
    return RedirectResponse(url=_safe_referer(request), status_code=303)


@app.post("/api/report/reset")
def reset_report(request: Request) -> Response:
    request.app.state.report = request.app.state.default_report
    rep = request.app.state.report
    if _wants_json(request):
        return JSONResponse({
            "ok": True,
            "source": rep["source"],
            "period": rep["period"]["label"],
        })
    return RedirectResponse(url=_safe_referer(request), status_code=303)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.ico", media_type="image/x-icon")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}

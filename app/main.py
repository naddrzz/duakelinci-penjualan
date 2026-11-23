"""FastAPI entry point. The CSV is loaded and analysed once, at startup."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .analysis import build_report
from .data import load_sales
from .formatting import month_label, month_short, pct, rp, rp_short

STATIC_DIR = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters.update(
    rp=rp, rp_short=rp_short, pct=pct, month_label=month_label, month_short=month_short
)


def asset_url(name: str) -> str:
    """URL of a static file with its modification time as a cache-busting version."""
    return f"/static/{name}?v={int((STATIC_DIR / name).stat().st_mtime)}"


templates.env.globals["asset_url"] = asset_url


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    rows, cleaning = load_sales(config.DATA_PATH)
    app.state.report = build_report(
        rows,
        cleaning,
        source=config.DATA_PATH.name,
        min_base_idr=config.MIN_BASE_SALES_IDR,
        weak_count=config.WEAK_OUTLET_COUNT,
    )
    yield


app = FastAPI(title="Dua Kelinci Sales Summary", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def render(request: Request, template: str, page: str, title: str, **extra: object) -> HTMLResponse:
    context = {"r": request.app.state.report, "page": page, "title": title, **extra}
    return templates.TemplateResponse(request, template, context)


@app.get("/", response_class=HTMLResponse)
def ringkasan(request: Request) -> HTMLResponse:
    return render(request, "ringkasan.html", "ringkasan", "Ringkasan")


@app.get("/wilayah-merek", response_class=HTMLResponse)
def wilayah_merek(request: Request, lihat: str = "wilayah") -> HTMLResponse:
    view = lihat if lihat in ("wilayah", "merek") else "wilayah"
    return render(request, "wilayah_merek.html", "wilayah-merek", "Wilayah dan merek", view=view)


@app.get("/outlet-terlemah", response_class=HTMLResponse)
def outlet_terlemah(request: Request) -> HTMLResponse:
    return render(request, "outlet_terlemah.html", "outlet-terlemah", "Outlet terlemah")


@app.get("/api/report")
def api_report(request: Request) -> dict:
    return request.app.state.report


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}

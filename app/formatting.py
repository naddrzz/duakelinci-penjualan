"""Indonesian number formatting for the page and the Telegram text."""

import re
from markupsafe import Markup, escape

MONTHS_ID = ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des")
MINUS = "−"
NBSP = "\u00a0"

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`\n]+)`")


def _id_decimal(text: str) -> str:
    """Swap '.' and ',' so 1,234.5 becomes 1.234,5."""
    return text.translate(str.maketrans({".": ",", ",": "."}))


def rp(value: int) -> str:
    """Full rupiah: Rp 1.725.966.000"""
    sign = MINUS if value < 0 else ""
    return f"{sign}Rp {_id_decimal(f'{abs(value):,}')}"


def rp_short(value: int) -> str:
    """Compact rupiah: Rp 1,73 miliar / Rp 495,8 jt / Rp 528 rb."""
    sign = MINUS if value < 0 else ""
    v = abs(value)
    if v >= 1_000_000_000:
        text = f"{v / 1e9:.2f} miliar"
    elif v >= 1_000_000:
        text = f"{v / 1e6:.1f} jt"
    elif v >= 1_000:
        text = f"{v / 1e3:.0f} rb"
    else:
        text = str(v)
    return f"{sign}Rp {_id_decimal(text)}"


def rp_tg(value: int) -> str:
    """Compact rupiah for Telegram (EYD V tight 'Rp' + NBSP unit glue): Rp1,73\u00a0miliar / −Rp6,3\u00a0jt."""
    sign = MINUS if value < 0 else ""
    v = abs(value)
    if v >= 1_000_000_000:
        text = f"{v / 1e9:.2f}{NBSP}miliar"
    elif v >= 1_000_000:
        text = f"{v / 1e6:.1f}{NBSP}jt"
    elif v >= 1_000:
        text = f"{v / 1e3:.0f}{NBSP}rb"
    else:
        text = str(v)
    return f"{sign}Rp{_id_decimal(text)}"


def tg_preview_html(text: str) -> Markup:
    """Render Telegram `**bold**` and `` `code` `` safely as HTML for the dashboard preview."""
    safe = str(escape(text))
    safe = _CODE_RE.sub(r'<code class="tg-code">\1</code>', safe)
    safe = _BOLD_RE.sub(r"<strong>\1</strong>", safe)
    return Markup(safe)


def pct(value: float | None, digits: int = 1, signed: bool = True) -> str:
    """Percentage with Indonesian decimal comma and a real minus sign: +3,6% / −68,7%."""
    if value is None:
        return "baru"
    text = f"{value:+.{digits}f}%" if signed else f"{value:.{digits}f}%"
    return _id_decimal(text).replace("-", MINUS)


def month_label(month: str) -> str:
    """'2026-09' -> 'Sep 2026'."""
    year, mon = month.split("-")
    return f"{MONTHS_ID[int(mon) - 1]} {year}"


def month_short(month: str) -> str:
    """'2026-09' -> 'Sep'."""
    return MONTHS_ID[int(month.split("-")[1]) - 1]


def date_id(iso_date: str) -> str:
    """'2026-10-31' -> '31 Okt 2026'."""
    if not iso_date:
        return "—"
    year, mon, day = iso_date.split("-")
    return f"{int(day)} {MONTHS_ID[int(mon) - 1]} {year}"


def period_label(months: list[str]) -> str:
    """['2026-09', '2026-10'] -> 'Sep–Okt 2026'."""
    first, last = months[0], months[-1]
    if first == last:
        return month_label(first)
    if first[:4] == last[:4]:
        return f"{month_short(first)}–{month_short(last)} {first[:4]}"
    return f"{month_label(first)}–{month_label(last)}"

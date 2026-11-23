"""Turn clean sales rows into the report shown on the page and returned by /api/report.

Metric definitions live in docs/metrics.md; keep the two in sync.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict

from .data import CleaningReport, Sale
from .formatting import month_short, period_label, pct, rp_short


def change_pct(base: int, current: int) -> float | None:
    """Percent change from base to current; None when there is no base to compare."""
    if base <= 0:
        return None
    return (current - base) / base * 100


def breakdown(rows: list[Sale], key: Callable[[Sale], str], months: list[str]) -> list[dict]:
    """Net sales per group and month, sorted by total net sales (highest first)."""
    by_group: dict[str, dict[str, int]] = defaultdict(lambda: dict.fromkeys(months, 0))
    for sale in rows:
        by_group[key(sale)][sale.month] += sale.net_sales_idr

    grand_total = sum(sale.net_sales_idr for sale in rows)
    base, current = months[-2], months[-1]
    lines = []
    for name, by_month in by_group.items():
        total = sum(by_month.values())
        lines.append({
            "name": name,
            "by_month": by_month,
            "total": total,
            "change_pct": change_pct(by_month[base], by_month[current]),
            "share_pct": total / grand_total * 100 if grand_total else 0.0,
        })
    lines.sort(key=lambda line: line["total"], reverse=True)
    return lines


def outlet_table(rows: list[Sale], base: str, current: str) -> list[dict]:
    """Every outlet with base vs current month net sales, worst % change first.

    Outlets are keyed by outlet_id because outlet names are not unique.
    Outlets with no base-month sales (new outlets) sort last.
    """
    outlets: dict[str, dict] = {}
    for sale in rows:
        o = outlets.setdefault(sale.outlet_id, {
            "outlet_id": sale.outlet_id,
            "name": sale.outlet_name,
            "branch": sale.branch,
            "region": sale.region,
            "outlet_type": sale.outlet_type,
            "base": 0,
            "current": 0,
        })
        if sale.month == base:
            o["base"] += sale.net_sales_idr
        elif sale.month == current:
            o["current"] += sale.net_sales_idr

    table = []
    for o in outlets.values():
        o["total"] = o["base"] + o["current"]
        o["change_idr"] = o["current"] - o["base"]
        o["change_pct"] = change_pct(o["base"], o["current"])
        table.append(o)
    table.sort(key=lambda o: (o["change_pct"] is None, o["change_pct"] or 0, o["change_idr"]))
    return table


def weakest_outlets(outlets: list[dict], min_base_idr: int, count: int) -> list[dict]:
    """The `count` outlets with the steepest % decline, among outlets that sold at
    least `min_base_idr` in the base month. Only declining outlets qualify."""
    candidates = [
        o for o in outlets
        if o["base"] >= min_base_idr and o["change_pct"] is not None and o["change_pct"] < 0
    ]
    candidates.sort(key=lambda o: (o["change_pct"], o["change_idr"]))
    return candidates[:count]


def weakest_analysis(outlets: list[dict], min_base_idr: int, count: int) -> dict:
    """How the weakest-outlet rule narrows all outlets down, step by step, plus the
    top `count` under two alternative definitions, for the explanation page."""
    new = [o for o in outlets if o["base"] <= 0]
    small = [o for o in outlets if 0 < o["base"] < min_base_idr]
    eligible = [o for o in outlets if o["base"] >= min_base_idr]
    declining = [o for o in eligible if o["change_idr"] < 0]
    return {
        "total": len(outlets),
        "new": new,
        "small": sorted(small, key=lambda o: o["base"]),
        "eligible": len(eligible),
        "declining": len(declining),
        "lowest_total": sorted(outlets, key=lambda o: o["total"])[:count],
        "largest_drop_idr": sorted(outlets, key=lambda o: o["change_idr"])[:count],
    }


def telegram_summary(report: dict) -> str:
    """Scannable multi-line summary for Telegram (Bahasa Indonesia, BLUF + numbered list)."""
    base, current = report["period"]["base"], report["period"]["current"]
    totals = report["totals"]
    region, brand = report["regions"][0], report["brands"][0]

    change = totals["change_pct"]
    if change is None or round(change, 1) == 0:
        trend = "stabil"
    else:
        trend = f"{'naik' if change > 0 else 'turun'} {pct(abs(change), signed=False)}"

    lines = [
        f"Ringkasan Penjualan Dua Kelinci — {report['period']['label']}",
        "",
        f"Total penjualan bersih: {rp_short(totals['net'])} ({trend})",
        f"• Perbandingan: {month_short(base)} {rp_short(totals['by_month'][base])} → {month_short(current)} {rp_short(totals['by_month'][current])}",
        f"• Wilayah terbaik: {region['name']} — {rp_short(region['total'])} ({pct(region['share_pct'], signed=False)} dari total)",
        f"• Merek terbaik: {brand['name']} — {rp_short(brand['total'])} ({pct(brand['share_pct'], signed=False)} dari total)",
        "",
    ]
    weakest = report["weakest"]
    if weakest:
        lines.append(
            f"Outlet perlu diperhatikan (penurunan terbesar {month_short(base)} → {month_short(current)}):"
        )
        for idx, o in enumerate(weakest, start=1):
            lines.append(
                f"{idx}. {o['name']}, {o['branch']} ({pct(o['change_pct'], digits=0)} · {rp_short(o['change_idr'])})"
            )
    else:
        lines.append(f"Tidak ada outlet yang turun dari {month_short(base)} ke {month_short(current)}.")
    return "\n".join(lines)


def build_report(
    rows: list[Sale],
    cleaning: CleaningReport,
    source: str,
    min_base_idr: int,
    weak_count: int,
) -> dict:
    """Everything the page and the API need, as JSON-serialisable data.

    Compares the last two months present in the data. Raises ValueError when the
    data has fewer than two months.
    """
    months = sorted({sale.month for sale in rows})
    if len(months) < 2:
        raise ValueError(f"{source}: need at least two months of data to compare, got {months}")
    base, current = months[-2], months[-1]

    by_month = dict.fromkeys(months, 0)
    for sale in rows:
        by_month[sale.month] += sale.net_sales_idr

    outlets = outlet_table(rows, base, current)
    report = {
        "source": source,
        "period": {
            "months": months,
            "label": period_label(months),
            "base": base,
            "current": current,
        },
        "totals": {
            "net": sum(by_month.values()),
            "gross": sum(s.gross_sales_idr for s in rows),
            "discount": sum(s.discount_idr for s in rows),
            "qty_carton": sum(s.qty_carton for s in rows),
            "invoices": len({s.invoice_no for s in rows}),
            "outlets": len(outlets),
            "by_month": by_month,
            "change_pct": change_pct(by_month[base], by_month[current]),
        },
        "regions": breakdown(rows, lambda s: s.region, months),
        "brands": breakdown(rows, lambda s: s.brand, months),
        "outlets": outlets,
        "weakest_rule": {"min_base_idr": min_base_idr, "count": weak_count},
        "weakest": weakest_outlets(outlets, min_base_idr, weak_count),
        "weakest_analysis": weakest_analysis(outlets, min_base_idr, weak_count),
        "data_quality": asdict(cleaning),
    }
    report["telegram_summary"] = telegram_summary(report)
    return report

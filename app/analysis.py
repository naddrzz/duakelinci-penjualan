"""Turn clean sales rows into the report shown on the page and returned by /api/report.

Metric definitions live in docs/metrics.md; keep the two in sync.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict
import statistics

from .data import CleaningReport, Sale
from .formatting import month_short, period_label, pct, rp_short


def adaptive_base_floor(outlets: list[dict]) -> int:
    """Compute the exact unrounded 1st quartile (Q1 / P25, position 0.25 * (N + 1))
    of active base-month outlets to suppress small-denominator noise (De Moivre's equation)
    without shifting the boundary via intermediate rounding.

    For tiny custom datasets (< 4 active outlets), quartile trimming does not apply (returns 0).
    """
    active_bases = sorted(o["base"] for o in outlets if o["base"] > 0)
    if len(active_bases) < 4:
        return 0
    q1_exact = int(round(statistics.quantiles(active_bases, n=4, method="exclusive")[0]))
    return max(0, q1_exact)


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
    """Every outlet with base vs current month net sales, operational activity, and % change.

    Outlets are keyed by outlet_id because outlet names are not unique.
    Outlets with no base-month sales (new outlets) sort last.
    """
    outlets: dict[str, dict] = {}
    inv_sets: dict[str, tuple[set[str], set[str]]] = {}
    sku_sets: dict[str, tuple[set[str], set[str]]] = {}

    for sale in rows:
        oid = sale.outlet_id
        o = outlets.setdefault(oid, {
            "outlet_id": oid,
            "name": sale.outlet_name,
            "branch": sale.branch,
            "region": sale.region,
            "outlet_type": sale.outlet_type,
            "base": 0,
            "current": 0,
        })
        b_inv, c_inv = inv_sets.setdefault(oid, (set(), set()))
        b_sku, c_sku = sku_sets.setdefault(oid, (set(), set()))
        if sale.month == base:
            o["base"] += sale.net_sales_idr
            b_inv.add(sale.invoice_no)
            if sale.qty_carton > 0:
                b_sku.add(sale.sku)
        elif sale.month == current:
            o["current"] += sale.net_sales_idr
            c_inv.add(sale.invoice_no)
            if sale.qty_carton > 0:
                c_sku.add(sale.sku)

    active_bases = [o["base"] for o in outlets.values() if o["base"] > 0]
    eb_prior_c = statistics.median(active_bases) if active_bases else 0.0
    total_base = sum(o["base"] for o in outlets.values())
    total_curr = sum(o["current"] for o in outlets.values())
    pop_ratio = total_curr / total_base if total_base > 0 else 1.0

    table = []
    for oid, o in outlets.items():
        b_inv, c_inv = inv_sets[oid]
        b_sku, c_sku = sku_sets[oid]
        o["base_invoices"] = len(b_inv)
        o["current_invoices"] = len(c_inv)
        o["base_skus"] = len(b_sku)
        o["current_skus"] = len(c_sku)
        o["total"] = o["base"] + o["current"]
        o["change_idr"] = o["current"] - o["base"]
        o["change_pct"] = change_pct(o["base"], o["current"])
        o["eb_change_pct"] = (
            ((o["current"] + eb_prior_c * pop_ratio) / (o["base"] + eb_prior_c) - 1) * 100
            if o["base"] > 0 and (o["base"] + eb_prior_c) > 0
            else None
        )
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
    """How the weakest-outlet rule narrows all outlets down, step by step, plus
    complementary FMCG lenses (steepest rupiah revenue loss, Empirical Bayes ranking,
    and lowest total sales for methodology comparison)."""
    new = [o for o in outlets if o["base"] <= 0]
    small = [o for o in outlets if 0 < o["base"] < min_base_idr]
    eligible = [o for o in outlets if o["base"] >= min_base_idr]
    declining = [o for o in eligible if o["change_idr"] < 0]
    all_declining = [o for o in outlets if o["base"] > 0 and o["change_idr"] < 0]
    total_drop_idr = sum(-o["change_idr"] for o in all_declining)
    top_drop_declining = sorted(all_declining, key=lambda o: (o["change_idr"], o["change_pct"] or 0))[:count]
    eb_declining = sorted(
        all_declining,
        key=lambda o: (o["eb_change_pct"] if o["eb_change_pct"] is not None else 0, o["change_idr"]),
    )[:count]
    return {
        "total": len(outlets),
        "new": new,
        "small": sorted(small, key=lambda o: o["base"]),
        "eligible": len(eligible),
        "declining": len(declining),
        "all_declining_count": len(all_declining),
        "total_drop_idr": total_drop_idr,
        "lowest_total": sorted(outlets, key=lambda o: o["total"])[:count],
        "largest_drop_idr": sorted(outlets, key=lambda o: o["change_idr"])[:count],
        "revenue_at_risk": top_drop_declining,
        "empirical_bayes": eb_declining,
    }


def telegram_summary(report: dict) -> str:
    """Scannable multi-line summary for Telegram (Bahasa Indonesia, BLUF + dual FMCG watch lenses)."""
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
    rev_risk = report["weakest_analysis"]["revenue_at_risk"]
    if weakest:
        lines.append(
            f"Outlet perlu perhatian — penurunan % terdalam ({month_short(base)} → {month_short(current)}):"
        )
        for idx, o in enumerate(weakest, start=1):
            lines.append(
                f"{idx}. {o['name']}, {o['branch']} ({pct(o['change_pct'], digits=0)} · {rp_short(o['change_idr'])})"
            )
        weak_ids = {o["outlet_id"] for o in weakest}
        extra_big_drops = [o for o in rev_risk[:3] if o["outlet_id"] not in weak_ids]
        if extra_big_drops:
            lines.append("")
            lines.append("Penurunan rupiah terbesar (akun besar):")
            for o in extra_big_drops:
                lines.append(
                    f"• {o['name']}, {o['branch']} ({rp_short(o['change_idr'])} · {pct(o['change_pct'], digits=0)})"
                )
    elif rev_risk:
        lines.append(
            f"Outlet dengan penurunan penjualan ({month_short(base)} → {month_short(current)}):"
        )
        for idx, o in enumerate(rev_risk, start=1):
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
    min_base_idr: int | None = None,
    weak_count: int = 5,
) -> dict:
    """Everything the page and the API need, as JSON-serialisable data.

    Compares the last two months present in the data. Raises ValueError when the
    data has fewer than two months. When `min_base_idr` is None, derives an adaptive
    Q1 (25th-percentile) materiality floor from active base-month outlets.
    """
    months = sorted({sale.month for sale in rows})
    if len(months) < 2:
        raise ValueError(f"{source}: need at least two months of data to compare, got {months}")
    base, current = months[-2], months[-1]

    by_month = dict.fromkeys(months, 0)
    for sale in rows:
        by_month[sale.month] += sale.net_sales_idr

    outlets = outlet_table(rows, base, current)
    q1_exact = adaptive_base_floor(outlets)
    effective_floor = q1_exact if min_base_idr is None else min_base_idr

    weak = weakest_outlets(outlets, effective_floor, weak_count)
    analysis = weakest_analysis(outlets, effective_floor, weak_count)
    total_drop = analysis["total_drop_idr"]
    weak_drop_sum = sum(-o["change_idr"] for o in weak)
    risk_drop_sum = sum(-o["change_idr"] for o in analysis["revenue_at_risk"])
    analysis["weakest_drop_idr"] = weak_drop_sum
    analysis["weakest_drop_share_pct"] = (weak_drop_sum / total_drop * 100) if total_drop > 0 else 0.0
    analysis["risk_drop_idr"] = risk_drop_sum
    analysis["risk_drop_share_pct"] = (risk_drop_sum / total_drop * 100) if total_drop > 0 else 0.0

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
        "weakest_rule": {
            "min_base_idr": effective_floor,
            "q1_base_idr": q1_exact,
            "adaptive": min_base_idr is None,
            "count": weak_count,
        },
        "weakest": weak,
        "weakest_analysis": analysis,
        "data_quality": asdict(cleaning),
    }
    report["telegram_summary"] = telegram_summary(report)
    return report

"""Turn clean sales rows into the report shown on the page and returned by /api/report.

Metric definitions live in docs/metrics.md; keep the two in sync.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict
import math
import statistics

from .data import UNASSIGNED_SALESMAN, CleaningReport, Sale
from .formatting import (
    month_full_label,
    month_full_name,
    month_short,
    period_label,
    pct,
    rp_prose,
    rp_short,
)

UNASSIGNED_LABEL = "Belum tercatat"


def display_salesman(raw_name: str) -> str:
    """Human-readable Bahasa Indonesia label for a salesman value."""
    return UNASSIGNED_LABEL if raw_name == UNASSIGNED_SALESMAN else raw_name


def adaptive_base_floor(outlets: list[dict]) -> int:
    """Return the 25th-percentile (Q1) base-month sales among active outlets.

    Excluding the smallest 25% of base-month outlets prevents tiny stores from
    dominating the % drop ranking over small rupiah changes, and scales automatically
    when a different CSV is uploaded. Returns 0 when fewer than 4 active outlets exist.
    """
    active_bases = sorted(o["base"] for o in outlets if o["base"] > 0)
    if len(active_bases) < 4:
        return 0
    q1_float = statistics.quantiles(active_bases, n=4, method="exclusive")[0]
    return max(0, math.ceil(q1_float))


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
            "change_idr": by_month[current] - by_month[base],
            "change_pct": change_pct(by_month[base], by_month[current]),
            "share_pct": total / grand_total * 100 if grand_total else 0.0,
        })
    lines.sort(key=lambda line: line["total"], reverse=True)
    return lines


def branch_breakdown(rows: list[Sale], months: list[str]) -> list[dict]:
    """Net sales per city branch with parent region, outlet count, and salesman roster."""
    lines = breakdown(rows, lambda s: s.branch, months)
    branch_region: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    branch_outlets: dict[str, set[str]] = defaultdict(set)
    branch_sm: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sale in rows:
        branch_region[sale.branch][sale.region] += abs(sale.net_sales_idr) or 1
        branch_outlets[sale.branch].add(sale.outlet_id)
        if sale.salesman != UNASSIGNED_SALESMAN:
            branch_sm[sale.branch][sale.salesman] += sale.net_sales_idr

    for line in lines:
        bname = line["name"]
        reg_counts = branch_region[bname]
        line["region"] = max(reg_counts, key=reg_counts.get) if reg_counts else ""
        line["outlets_count"] = len(branch_outlets[bname])
        sm_ranked = sorted(branch_sm[bname].items(), key=lambda kv: (-kv[1], kv[0]))
        sm_names = [name for name, _ in sm_ranked] or [UNASSIGNED_LABEL]
        line["salesmen"] = sm_names
        line["salesmen_label"] = ", ".join(sm_names)
        line["top_salesman"] = (
            {"name": sm_ranked[0][0], "total": sm_ranked[0][1]}
            if sm_ranked
            else {"name": UNASSIGNED_LABEL, "total": line["total"]}
        )
    return lines


def region_breakdown(rows: list[Sale], months: list[str], branches: list[dict]) -> list[dict]:
    """Net sales per region (branch group area), enriched with child city branches and top salesman."""
    lines = breakdown(rows, lambda s: s.region, months)
    reg_outlets: dict[str, set[str]] = defaultdict(set)
    reg_sm: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sm_branch: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sale in rows:
        reg_outlets[sale.region].add(sale.outlet_id)
        if sale.salesman != UNASSIGNED_SALESMAN:
            reg_sm[sale.region][sale.salesman] += sale.net_sales_idr
            sm_branch[sale.salesman][sale.branch] += abs(sale.net_sales_idr) or 1

    branches_by_region: dict[str, list[dict]] = defaultdict(list)
    for br in branches:
        branches_by_region[br["region"]].append(br)

    for line in lines:
        rname = line["name"]
        r_total = line["total"]
        child_branches = [
            {
                "name": br["name"],
                "total": br["total"],
                "by_month": br["by_month"],
                "change_idr": br["change_idr"],
                "change_pct": br["change_pct"],
                "share_pct": br["share_pct"],
                "share_of_region_pct": (br["total"] / r_total * 100) if r_total else 0.0,
                "salesmen_label": br["salesmen_label"],
            }
            for br in branches_by_region.get(rname, [])
        ]
        line["branches"] = child_branches
        line["top_branch"] = child_branches[0] if child_branches else None
        line["branches_label"] = ", ".join(b["name"] for b in child_branches)
        line["outlets_count"] = len(reg_outlets[rname])

        sm_ranked = sorted(reg_sm[rname].items(), key=lambda kv: (-kv[1], kv[0]))
        line["salesmen_count"] = len(sm_ranked)
        if sm_ranked:
            top_sm_name, top_sm_tot = sm_ranked[0]
            top_sm_br = max(sm_branch[top_sm_name], key=sm_branch[top_sm_name].get)
            line["top_salesman"] = {"name": top_sm_name, "branch": top_sm_br, "total": top_sm_tot}
        else:
            line["top_salesman"] = {"name": UNASSIGNED_LABEL, "branch": "", "total": r_total}
    return lines


def brand_breakdown(rows: list[Sale], months: list[str]) -> list[dict]:
    """Net sales per brand, enriched with strongest region, city branch, and salesman."""
    lines = breakdown(rows, lambda s: s.brand, months)
    brand_reg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    brand_br: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    brand_sm: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    brand_outlets: dict[str, set[str]] = defaultdict(set)
    sm_branch: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sale in rows:
        brand_reg[sale.brand][sale.region] += sale.net_sales_idr
        brand_br[sale.brand][sale.branch] += sale.net_sales_idr
        brand_outlets[sale.brand].add(sale.outlet_id)
        if sale.salesman != UNASSIGNED_SALESMAN:
            brand_sm[sale.brand][sale.salesman] += sale.net_sales_idr
            sm_branch[sale.salesman][sale.branch] += abs(sale.net_sales_idr) or 1

    for line in lines:
        bname = line["name"]
        reg_ranked = sorted(brand_reg[bname].items(), key=lambda kv: (-kv[1], kv[0]))
        br_ranked = sorted(brand_br[bname].items(), key=lambda kv: (-kv[1], kv[0]))
        sm_ranked = sorted(brand_sm[bname].items(), key=lambda kv: (-kv[1], kv[0]))
        line["outlets_count"] = len(brand_outlets[bname])
        line["top_region"] = {"name": reg_ranked[0][0], "total": reg_ranked[0][1]} if reg_ranked else None
        line["top_branch"] = {"name": br_ranked[0][0], "total": br_ranked[0][1]} if br_ranked else None
        if sm_ranked:
            sm_name, sm_tot = sm_ranked[0]
            sm_br = max(sm_branch[sm_name], key=sm_branch[sm_name].get)
            line["top_salesman"] = {"name": sm_name, "branch": sm_br, "total": sm_tot}
        else:
            line["top_salesman"] = {"name": UNASSIGNED_LABEL, "branch": "", "total": line["total"]}
    return lines


def salesman_breakdown(rows: list[Sale], months: list[str]) -> list[dict]:
    """Net sales per salesman with territory (branch & region), outlet count, and top brand."""
    raw_lines = breakdown(rows, lambda s: s.salesman, months)
    sm_reg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sm_br: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sm_brand: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sm_outlets: dict[str, set[str]] = defaultdict(set)

    for sale in rows:
        sm_reg[sale.salesman][sale.region] += abs(sale.net_sales_idr) or 1
        sm_br[sale.salesman][sale.branch] += abs(sale.net_sales_idr) or 1
        sm_brand[sale.salesman][sale.brand] += sale.net_sales_idr
        sm_outlets[sale.salesman].add(sale.outlet_id)

    named: list[dict] = []
    unassigned: list[dict] = []
    for line in raw_lines:
        raw_name = line["name"]
        is_unassigned = raw_name == UNASSIGNED_SALESMAN
        regs = sorted(sm_reg[raw_name].items(), key=lambda kv: (-kv[1], kv[0]))
        brs = sorted(sm_br[raw_name].items(), key=lambda kv: (-kv[1], kv[0]))
        brands = sorted(sm_brand[raw_name].items(), key=lambda kv: (-kv[1], kv[0]))

        enriched = {
            **line,
            "raw_name": raw_name,
            "name": display_salesman(raw_name),
            "is_unassigned": is_unassigned,
            "region": regs[0][0] if regs and not is_unassigned else ("Lintas wilayah" if len(regs) > 1 else (regs[0][0] if regs else "")),
            "branch": brs[0][0] if brs and not is_unassigned else ("Beberapa cabang" if len(brs) > 1 else (brs[0][0] if brs else "")),
            "branches_label": ", ".join(b for b, _ in brs),
            "outlets_count": len(sm_outlets[raw_name]),
            "top_brand": brands[0][0] if brands else "",
            "brands_label": ", ".join(b for b, _ in brands),
        }
        if is_unassigned:
            unassigned.append(enriched)
        else:
            named.append(enriched)

    # Named salesmen rank by total descending; unassigned rows stay transparent at the bottom.
    return named + unassigned


def _build_salesman_drop_note(sm_list: list[dict], outlet_change_idr: int) -> str:
    """Summarize which salesman drove an outlet's decline when `outlet_change_idr < 0`."""
    if outlet_change_idr >= 0 or not sm_list:
        return ""
    if len(sm_list) == 1:
        only = sm_list[0]
        if only["base"] > 0 and only["current"] <= 0:
            return f"berhenti order dari {rp_short(only['base'])}"
        return ""

    by_drop = sorted(sm_list, key=lambda s: (s["change_idr"], s["change_pct"] or 0))
    worst = by_drop[0]
    if worst["change_idr"] >= 0:
        return ""
    if worst["base"] > 0 and worst["current"] <= 0:
        return f"{worst['name']} berhenti order dari {rp_short(worst['base'])}"

    others_up = any(s["change_idr"] >= 0 for s in by_drop[1:])
    dominant = abs(worst["change_idr"]) >= 0.65 * abs(outlet_change_idr)
    if others_up or dominant:
        pct_part = f" ({pct(worst['change_pct'], digits=0)})" if worst["change_pct"] is not None else ""
        return f"{worst['name']} turun {rp_short(abs(worst['change_idr']))}{pct_part}"

    return ", ".join(
        f"{s['name']} {rp_short(s['change_idr'])}" for s in by_drop[:2] if s["change_idr"] < 0
    )


def outlet_table(rows: list[Sale], base: str, current: str) -> list[dict]:
    """Every outlet with base vs current month net sales, salesman roster, operational activity, and % change.

    Outlets are keyed by outlet_id because outlet names are not unique.
    Outlets with no base-month sales (new outlets) sort last.
    """
    outlets: dict[str, dict] = {}
    inv_sets: dict[str, tuple[set[str], set[str]]] = {}
    sku_sets: dict[str, tuple[set[str], set[str]]] = {}
    brand_sets: dict[str, set[str]] = defaultdict(set)
    sm_ledger: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"base": 0, "current": 0, "all": 0})
    )
    sku_ledger: dict[str, dict[str, dict]] = defaultdict(dict)
    last_order_meta: dict[str, tuple] = {}

    for sale in rows:
        oid = sale.outlet_id
        brand_sets[oid].add(sale.brand)
        o = outlets.setdefault(oid, {
            "outlet_id": oid,
            "name": sale.outlet_name,
            "branch": sale.branch,
            "region": sale.region,
            "outlet_type": sale.outlet_type,
            "base": 0,
            "current": 0,
            "base_cartons": 0,
            "current_cartons": 0,
            "base_discount": 0,
            "current_discount": 0,
            "return_rows": 0,
            "return_net_idr": 0,
        })
        b_inv, c_inv = inv_sets.setdefault(oid, (set(), set()))
        b_sku, c_sku = sku_sets.setdefault(oid, (set(), set()))
        sm_entry = sm_ledger[oid][sale.salesman]
        sm_entry["all"] += sale.net_sales_idr

        sku_entry = sku_ledger[oid].setdefault(sale.sku, {
            "sku": sale.sku,
            "brand": sale.brand,
            "base": 0,
            "current": 0,
            "base_cartons": 0,
            "current_cartons": 0,
            "salesmen": set(),
        })
        if sale.salesman != UNASSIGNED_SALESMAN:
            sku_entry["salesmen"].add(sale.salesman)

        if sale.qty_carton > 0:
            prev_last = last_order_meta.get(oid)
            if prev_last is None or (sale.date, sale.invoice_no) >= (prev_last[0], prev_last[2]):
                last_order_meta[oid] = (sale.date, display_salesman(sale.salesman), sale.invoice_no)
        elif sale.qty_carton < 0 and sale.month in (base, current):
            o["return_rows"] += 1
            o["return_net_idr"] += sale.net_sales_idr

        if sale.month == base:
            o["base"] += sale.net_sales_idr
            o["base_cartons"] += sale.qty_carton
            o["base_discount"] += sale.discount_idr
            sm_entry["base"] += sale.net_sales_idr
            sku_entry["base"] += sale.net_sales_idr
            sku_entry["base_cartons"] += sale.qty_carton
            if sale.qty_carton > 0:
                b_inv.add(sale.invoice_no)
                b_sku.add(sale.sku)
        elif sale.month == current:
            o["current"] += sale.net_sales_idr
            o["current_cartons"] += sale.qty_carton
            o["current_discount"] += sale.discount_idr
            sm_entry["current"] += sale.net_sales_idr
            sku_entry["current"] += sale.net_sales_idr
            sku_entry["current_cartons"] += sale.qty_carton
            if sale.qty_carton > 0:
                c_inv.add(sale.invoice_no)
                c_sku.add(sale.sku)

    table = []
    for oid, o in outlets.items():
        b_inv, c_inv = inv_sets[oid]
        b_sku, c_sku = sku_sets[oid]
        o["base_invoices"] = len(b_inv)
        o["current_invoices"] = len(c_inv)
        o["base_skus"] = len(b_sku)
        o["current_skus"] = len(c_sku)
        o["change_cartons"] = o["current_cartons"] - o["base_cartons"]
        o["carton_change_pct"] = change_pct(o["base_cartons"], o["current_cartons"])
        o["base_avg_invoice_idr"] = round(o["base"] / o["base_invoices"]) if o["base_invoices"] > 0 else 0
        o["current_avg_invoice_idr"] = round(o["current"] / o["current_invoices"]) if o["current_invoices"] > 0 else 0
        last_meta = last_order_meta.get(oid)
        o["last_order_date"] = last_meta[0].isoformat() if last_meta else ""
        o["last_order_salesman"] = last_meta[1] if last_meta else ""
        o["last_order_invoice"] = last_meta[2] if last_meta else ""
        o["total"] = o["base"] + o["current"]
        o["change_idr"] = o["current"] - o["base"]
        o["change_pct"] = change_pct(o["base"], o["current"])

        raw_sm_map = sm_ledger[oid]
        has_named = any(k != UNASSIGNED_SALESMAN for k in raw_sm_map)
        sm_items = []
        for raw_sm, vals in raw_sm_map.items():
            if has_named and raw_sm == UNASSIGNED_SALESMAN:
                continue
            sm_base, sm_curr = vals["base"], vals["current"]
            sm_tot = sm_base + sm_curr
            sm_items.append({
                "name": display_salesman(raw_sm),
                "base": sm_base,
                "current": sm_curr,
                "total": sm_tot if sm_tot != 0 else vals["all"],
                "change_idr": sm_curr - sm_base,
                "change_pct": change_pct(sm_base, sm_curr),
            })
        sm_items.sort(key=lambda item: (-item["total"], item["name"]))
        sm_names = [item["name"] for item in sm_items] or [UNASSIGNED_LABEL]
        o["salesmen"] = sm_items
        o["salesman_names"] = sm_names
        o["salesman"] = ", ".join(sm_names)
        o["lead_salesman"] = sm_names[0]
        o["brands_label"] = ", ".join(sorted(brand_sets[oid]))
        o["salesman_drop_note"] = _build_salesman_drop_note(sm_items, o["change_idr"])

        sku_items = []
        stopped_cnt = declining_cnt = growing_cnt = new_cnt = stopped_idr = 0
        for sku_name, sv in sku_ledger[oid].items():
            s_base, s_curr = sv["base"], sv["current"]
            sb_ctn, sc_ctn = sv["base_cartons"], sv["current_cartons"]
            has_base = sku_name in b_sku or s_base > 0
            has_curr = sku_name in c_sku or s_curr > 0
            if not has_base and not has_curr and s_base == 0 and s_curr == 0:
                continue
            if has_base and not has_curr:
                s_status, s_group = "berhenti", "berhenti"
                stopped_cnt += 1
                stopped_idr += s_curr - s_base
            elif not has_base and has_curr:
                s_status, s_group = "baru", "jalan"
                new_cnt += 1
            elif s_curr < s_base:
                s_status, s_group = "turun", "jalan"
                declining_cnt += 1
            elif s_curr > s_base:
                s_status, s_group = "tumbuh", "jalan"
                growing_cnt += 1
            else:
                s_status, s_group = "stabil", "jalan"
                growing_cnt += 1

            s_sales = sorted(sv["salesmen"])
            sku_items.append({
                "sku": sku_name,
                "brand": sv["brand"],
                "base": s_base,
                "current": s_curr,
                "total": s_base + s_curr,
                "change_idr": s_curr - s_base,
                "change_pct": change_pct(s_base, s_curr),
                "base_cartons": sb_ctn,
                "current_cartons": sc_ctn,
                "change_cartons": sc_ctn - sb_ctn,
                "salesman_label": ", ".join(s_sales) if s_sales else UNASSIGNED_LABEL,
                "status": s_status,
                "group": s_group,
            })

        status_rank = {"berhenti": 0, "turun": 1, "tumbuh": 2, "baru": 3, "stabil": 4}
        sku_items.sort(
            key=lambda item: (
                status_rank[item["status"]],
                item["change_idr"] if item["status"] in ("berhenti", "turun") else -item["change_idr"],
                -item["current"],
                item["sku"],
            )
        )
        o["skus"] = sku_items
        o["sku_summary"] = {
            "total": len(sku_items),
            "stopped": stopped_cnt,
            "stopped_idr": stopped_idr,
            "running": declining_cnt + growing_cnt + new_cnt,
            "retained": declining_cnt + growing_cnt,
            "declining": declining_cnt,
            "growing": growing_cnt,
            "new": new_cnt,
        }

        table.append(o)
    table.sort(key=lambda o: (o["change_pct"] is None, o["change_pct"] or 0, o["change_idr"]))
    return table


def weakest_outlets(outlets: list[dict], min_base_idr: int, count: int) -> list[dict]:
    """The `count` outlets with the steepest % decline, among active base-month outlets
    that sold at least `min_base_idr`. Only declining outlets qualify."""
    candidates = [
        o for o in outlets
        if o["base"] > 0 and o["base"] >= min_base_idr and o["change_pct"] is not None and o["change_pct"] < 0
    ]
    candidates.sort(key=lambda o: (o["change_pct"], o["change_idr"]))
    return candidates[:count]


def weakest_analysis(outlets: list[dict], min_base_idr: int, count: int) -> dict:
    """How the weakest-outlet rule narrows all outlets down step by step, plus
    the top Rupiah drops across all active declining outlets."""
    new = [o for o in outlets if o["base"] <= 0]
    small = [o for o in outlets if 0 < o["base"] < min_base_idr]
    eligible = [o for o in outlets if o["base"] > 0 and o["base"] >= min_base_idr]
    declining = [o for o in eligible if o["change_idr"] < 0]
    all_declining = [o for o in outlets if o["base"] > 0 and o["change_idr"] < 0]
    total_drop_idr = sum(-o["change_idr"] for o in all_declining)
    top_drop_declining = sorted(all_declining, key=lambda o: (o["change_idr"], o["change_pct"] or 0))[:count]
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
    }


_NUM_WORDS_ID = {
    1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima", 6: "enam",
    7: "tujuh", 8: "delapan", 9: "sembilan", 10: "sepuluh", 11: "sebelas", 12: "dua belas",
}


def _num_word_id(n: int) -> str:
    return _NUM_WORDS_ID.get(n, str(n))


def _join_id(items: list[str], final_conj: str = "dan") -> str:
    """Join Indonesian list items naturally: 'A', 'A dan B', or 'A, B, dan C'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} dan {items[1]}"
    return f"{', '.join(items[:-1])}, {final_conj} {items[-1]}"


def _drop_salesman_tag(outlet: dict) -> str:
    """Return ', sales <Name>' for the salesman with the largest rupiah drop at this outlet."""
    named = [s for s in outlet.get("salesmen", []) if s["name"] != UNASSIGNED_LABEL]
    if not named:
        return ""
    worst = min(named, key=lambda s: (s["change_idr"], s["change_pct"] or 0))
    return f", sales {worst['name']}"


def telegram_summary(report: dict) -> str:
    """One-paragraph Bahasa Indonesia summary ready to read in Telegram."""
    base, current = report["period"]["base"], report["period"]["current"]
    cur_lbl = month_full_label(current)
    base_ref = month_full_name(base) if base[:4] == current[:4] else month_full_label(base)
    totals = report["totals"]

    cur_net = rp_prose(totals["by_month"][current])
    change = totals["change_pct"]
    if change is None or round(change, 1) == 0:
        sentences = [f"Penjualan bersih {cur_lbl} **{cur_net}**, stabil dari {base_ref}."]
    else:
        verb = "naik" if change > 0 else "turun"
        sentences = [
            f"Penjualan bersih {cur_lbl} **{cur_net}**, "
            f"{verb} {pct(abs(change), signed=False)} dari {base_ref}."
        ]

    regions = report["regions"]
    n_reg = len(regions)
    reg_with_pct = [r for r in regions if r["change_pct"] is not None]
    growing_regs = sorted(
        [r for r in reg_with_pct if r["change_idr"] > 0],
        key=lambda r: (-r["change_pct"], -r["change_idr"]),
    )
    declining_regs = sorted(
        [r for r in reg_with_pct if r["change_idr"] < 0],
        key=lambda r: (r["change_pct"], r["change_idr"]),
    )

    if growing_regs and declining_regs:
        top_up = growing_regs[0]
        up_pct = pct(abs(top_up["change_pct"]), digits=0, signed=False)
        top_down = declining_regs[0]
        down_pct = pct(abs(top_down["change_pct"]), digits=0, signed=False)
        if len(declining_regs) >= 2:
            sentences.append(
                f"{top_up['name']} naik {up_pct}, tetapi {_num_word_id(len(declining_regs))} dari "
                f"{_num_word_id(n_reg)} wilayah turun, terdalam {top_down['name']} ({down_pct})."
            )
        elif n_reg == 2:
            sentences.append(f"{top_up['name']} naik {up_pct}, tetapi {top_down['name']} turun {down_pct}.")
        else:
            sentences.append(
                f"{top_up['name']} naik {up_pct}, tetapi satu dari {_num_word_id(n_reg)} wilayah "
                f"turun yaitu {top_down['name']} ({down_pct})."
            )
    elif growing_regs:
        top_up = growing_regs[0]
        up_pct = pct(abs(top_up["change_pct"]), digits=0, signed=False)
        if n_reg > 1:
            sentences.append(f"Seluruh {_num_word_id(n_reg)} wilayah naik, tertinggi {top_up['name']} ({up_pct}).")
        else:
            sentences.append(f"Wilayah {top_up['name']} naik {up_pct}.")
    elif declining_regs:
        top_down = declining_regs[0]
        down_pct = pct(abs(top_down["change_pct"]), digits=0, signed=False)
        if n_reg > 1:
            sentences.append(f"Seluruh {_num_word_id(n_reg)} wilayah turun, terdalam {top_down['name']} ({down_pct}).")
        else:
            sentences.append(f"Wilayah {top_down['name']} turun {down_pct}.")

    weakest = report["weakest"]
    rev_risk = report["weakest_analysis"]["revenue_at_risk"]
    if weakest:
        cnt_word = _num_word_id(len(weakest)).capitalize()
        weak_parts = [
            f"{o['name']} `{o['outlet_id']}` {o['branch']} "
            f"({pct(abs(o['change_pct']), digits=0, signed=False)}{_drop_salesman_tag(o)})"
            for o in weakest
        ]
        sentences.append(f"**{cnt_word} outlet turun terdalam:** {_join_id(weak_parts, 'dan')}.")

        weak_ids = {o["outlet_id"] for o in weakest}
        extra_big_drops = [o for o in rev_risk[:2] if o["outlet_id"] not in weak_ids]
        if extra_big_drops:
            big_parts = [
                f"{o['name']} {o['branch']} ({rp_prose(abs(o['change_idr']))}{_drop_salesman_tag(o)})"
                for o in extra_big_drops
            ]
            sentences.append(f"**Rupiah terbesar hilang** di {_join_id(big_parts, 'dan')}.")
    elif rev_risk:
        top_risk = rev_risk[:5]
        cnt_word = _num_word_id(len(top_risk)).capitalize()
        risk_parts = [
            f"{o['name']} `{o['outlet_id']}` {o['branch']} "
            f"({pct(abs(o['change_pct']), digits=0, signed=False)}{_drop_salesman_tag(o)})"
            for o in top_risk
        ]
        sentences.append(f"**{cnt_word} outlet turun terdalam:** {_join_id(risk_parts, 'dan')}.")
    else:
        sentences.append(f"Seluruh outlet stabil atau naik dari {base_ref}.")

    return " ".join(sentences)


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

    branches = branch_breakdown(rows, months)
    regions = region_breakdown(rows, months, branches)
    brands = brand_breakdown(rows, months)
    salesmen = salesman_breakdown(rows, months)
    named_salesmen = [s for s in salesmen if not s["is_unassigned"]]

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

    outlets_by_total = sorted(outlets, key=lambda o: (-o["total"], o["outlet_id"]))
    sm_with_change = [s for s in named_salesmen if s["change_pct"] is not None]
    sm_by_pct = sorted(sm_with_change, key=lambda s: (s["change_pct"], s["change_idr"]))

    extremes = {
        "highest_outlet": outlets_by_total[0],
        "lowest_outlet": outlets_by_total[-1],
        "best_region": regions[0],
        "lowest_region": regions[-1],
        "best_branch": branches[0],
        "lowest_branch": branches[-1],
        "best_brand": brands[0],
        "lowest_brand": brands[-1],
        "best_salesman": named_salesmen[0] if named_salesmen else None,
        "lowest_salesman": named_salesmen[-1] if named_salesmen else None,
        "fastest_salesman": sm_by_pct[-1] if sm_by_pct else None,
        "steepest_drop_salesman": sm_by_pct[0] if sm_by_pct else None,
    }

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
            "branches": len(branches),
            "salesmen": len(named_salesmen) if named_salesmen else len(salesmen),
            "by_month": by_month,
            "change_pct": change_pct(by_month[base], by_month[current]),
        },
        "regions": regions,
        "branches": branches,
        "brands": brands,
        "salesmen": salesmen,
        "named_salesmen": named_salesmen,
        "extremes": extremes,
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

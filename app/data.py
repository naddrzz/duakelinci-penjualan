"""Load and clean the sales CSV. Cleaning rules are documented in docs/data.md."""

import csv
import io
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = (
    "date", "invoice_no", "region", "branch", "outlet_id", "outlet_name",
    "outlet_type", "salesman", "brand", "sku", "qty_carton",
    "price_per_carton_idr", "gross_sales_idr", "discount_idr", "net_sales_idr",
)
INT_COLUMNS = (
    "qty_carton", "price_per_carton_idr", "gross_sales_idr", "discount_idr", "net_sales_idr",
)

# Lower-cased spelling -> canonical region name. Add new aliases here.
REGIONS = {
    "jabodetabek": "Jabodetabek",
    "jawa barat": "Jawa Barat",
    "jabar": "Jawa Barat",
    "jawa tengah": "Jawa Tengah",
    "jawa timur": "Jawa Timur",
    "sumatera": "Sumatera",
    "kalimantan": "Kalimantan",
}

UNASSIGNED_SALESMAN = "(unassigned)"


@dataclass(frozen=True)
class Sale:
    date: date
    invoice_no: str
    region: str
    branch: str
    outlet_id: str
    outlet_name: str
    outlet_type: str
    salesman: str
    brand: str
    sku: str
    qty_carton: int
    price_per_carton_idr: int
    gross_sales_idr: int
    discount_idr: int
    net_sales_idr: int

    @property
    def month(self) -> str:
        return self.date.strftime("%Y-%m")


@dataclass
class CleaningReport:
    raw_rows: int = 0
    clean_rows: int = 0
    duplicates_removed: int = 0
    duplicates_net_idr: int = 0
    regions_normalized: int = 0
    text_trimmed: int = 0
    blank_salesman: int = 0
    return_rows: int = 0
    returns_net_idr: int = 0
    amount_mismatches: int = 0
    unknown_regions: list[str] = field(default_factory=list)


def load_sales(path: Path) -> tuple[list[Sale], CleaningReport]:
    """Read the CSV from disk, apply cleaning rules and return clean rows plus a report.

    Raises ValueError on a missing column or a value that cannot be parsed.
    """
    text = path.read_text(encoding="utf-8-sig")
    return load_sales_text(text, source_name=path.name)


def load_sales_text(text: str, source_name: str = "upload.csv") -> tuple[list[Sale], CleaningReport]:
    """Parse CSV text in memory using the exact same cleaning rules as load_sales().

    Supports standard comma-delimited CSVs as well as semicolon-delimited CSVs
    exported by Excel under Indonesian regional settings.
    """
    report = CleaningReport()
    rows: list[Sale] = []
    seen: set[Sale] = set()

    first_line = text.partition("\n")[0]
    delimiter = ";" if ("," not in first_line and ";" in first_line) else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"{source_name}: missing columns {missing}")

    for line_no, raw in enumerate(reader, start=2):
        if not any((v or "").strip() for v in raw.values()):
            continue
        report.raw_rows += 1
        sale = _parse_row(raw, line_no, report)
        if sale in seen:
            report.duplicates_removed += 1
            report.duplicates_net_idr += sale.net_sales_idr
            continue
        seen.add(sale)
        rows.append(sale)

    for sale in rows:
        if sale.qty_carton < 0:
            report.return_rows += 1
            report.returns_net_idr += sale.net_sales_idr
    report.clean_rows = len(rows)
    report.unknown_regions.sort()
    return rows, report


def _parse_row(raw: dict[str, str], line_no: int, report: CleaningReport) -> Sale:
    values = {k: (raw.get(k) or "") for k in REQUIRED_COLUMNS}
    if any(v != v.strip() for v in values.values()):
        report.text_trimmed += 1
    values = {k: v.strip() for k, v in values.items()}

    region = REGIONS.get(values["region"].lower())
    if region is None:
        region = values["region"].title()
        if region not in report.unknown_regions:
            report.unknown_regions.append(region)
    if region != values["region"]:
        report.regions_normalized += 1
    values["region"] = region

    if not values["salesman"]:
        report.blank_salesman += 1
        values["salesman"] = UNASSIGNED_SALESMAN

    try:
        parsed_date = date.fromisoformat(values["date"])
        nums = {k: int(values[k]) for k in INT_COLUMNS}
    except ValueError as exc:
        raise ValueError(f"line {line_no}: {exc}") from exc

    if (
        nums["qty_carton"] * nums["price_per_carton_idr"] != nums["gross_sales_idr"]
        or nums["gross_sales_idr"] - nums["discount_idr"] != nums["net_sales_idr"]
    ):
        report.amount_mismatches += 1

    return Sale(
        date=parsed_date,
        invoice_no=values["invoice_no"],
        region=values["region"],
        branch=values["branch"],
        outlet_id=values["outlet_id"],
        outlet_name=values["outlet_name"],
        outlet_type=values["outlet_type"],
        salesman=values["salesman"],
        brand=values["brand"],
        sku=values["sku"],
        qty_carton=nums["qty_carton"],
        price_per_carton_idr=nums["price_per_carton_idr"],
        gross_sales_idr=nums["gross_sales_idr"],
        discount_idr=nums["discount_idr"],
        net_sales_idr=nums["net_sales_idr"],
    )

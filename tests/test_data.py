from pathlib import Path

import pytest

from app.data import UNASSIGNED_SALESMAN, load_sales, load_sales_text

HEADER = (
    "date,invoice_no,region,branch,outlet_id,outlet_name,outlet_type,salesman,brand,sku,"
    "qty_carton,price_per_carton_idr,gross_sales_idr,discount_idr,net_sales_idr\n"
)
ROW = "2026-09-01,INV1,{region},Bandung,OUT1,{name},Grosir,{salesman},Sukro,Sukro Pedas 100g,{qty},186000,{gross},0,{gross}\n"


def write_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "sales.csv"
    path.write_text(HEADER + "".join(rows), encoding="utf-8")
    return path


def row(region="Jawa Barat", name="Grosir Sentosa", salesman="Hendra", qty=1) -> str:
    return ROW.format(region=region, name=name, salesman=salesman, qty=qty, gross=qty * 186000)


def test_region_aliases_and_case_are_normalised(tmp_path):
    path = write_csv(tmp_path, row("Jabar"), row("JAWA BARAT", qty=2), row("jabodetabek", qty=3))
    rows, report = load_sales(path)
    assert [r.region for r in rows] == ["Jawa Barat", "Jawa Barat", "Jabodetabek"]
    assert report.regions_normalized == 3
    assert report.unknown_regions == []


def test_unknown_region_is_kept_and_reported(tmp_path):
    rows, report = load_sales(write_csv(tmp_path, row("bali nusra")))
    assert rows[0].region == "Bali Nusra"
    assert report.unknown_regions == ["Bali Nusra"]


def test_whitespace_trimmed_before_duplicate_check(tmp_path):
    rows, report = load_sales(write_csv(tmp_path, row(name="Grosir Sentosa "), row()))
    assert len(rows) == 1
    assert rows[0].outlet_name == "Grosir Sentosa"
    assert report.text_trimmed == 1
    assert report.duplicates_removed == 1


def test_exact_duplicates_removed_but_distinct_rows_kept(tmp_path):
    rows, report = load_sales(write_csv(tmp_path, row(), row(), row(qty=2)))
    assert len(rows) == 2
    assert report.duplicates_removed == 1
    assert report.duplicates_net_idr == 186000


def test_returns_are_kept(tmp_path):
    rows, report = load_sales(write_csv(tmp_path, row(qty=-2)))
    assert rows[0].net_sales_idr == -372000
    assert report.return_rows == 1
    assert report.returns_net_idr == -372000


def test_blank_salesman_marked_unassigned(tmp_path):
    rows, report = load_sales(write_csv(tmp_path, row(salesman="")))
    assert rows[0].salesman == UNASSIGNED_SALESMAN
    assert report.blank_salesman == 1


def test_amount_mismatch_counted(tmp_path):
    bad = "2026-09-01,INV1,Jawa Barat,Bandung,OUT1,X,Grosir,H,Sukro,S,2,100,999,0,999\n"
    _, report = load_sales(write_csv(tmp_path, bad))
    assert report.amount_mismatches == 1


def test_missing_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,region\n2026-09-01,Jabar\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_sales(path)


def test_unparseable_number_raises_with_line(tmp_path):
    path = write_csv(tmp_path, row().replace(",1,186000", ",abc,186000"))
    with pytest.raises(ValueError, match="line 2"):
        load_sales(path)


def test_semicolon_delimited_csv_supported():
    semi_text = (HEADER + row("Jabar", qty=3) + "\n").replace(",", ";")
    rows, report = load_sales_text(semi_text, source_name="excel_id.csv")
    assert len(rows) == 1
    assert rows[0].region == "Jawa Barat"
    assert rows[0].qty_carton == 3
    assert report.clean_rows == 1


def test_real_file_cleaning_report(sales):
    _, report = sales
    assert report.raw_rows == 1891
    assert report.clean_rows == 1888
    assert report.duplicates_removed == 3
    assert report.duplicates_net_idr == 2_070_900
    assert report.regions_normalized == 10
    assert report.text_trimmed == 4
    assert report.blank_salesman == 5
    assert report.return_rows == 1
    assert report.returns_net_idr == -528_000
    assert report.amount_mismatches == 0
    assert report.unknown_regions == []

import pytest

from app import config
from app.analysis import build_report
from app.data import load_sales


@pytest.fixture(scope="session")
def sales():
    return load_sales(config.DATA_PATH)


@pytest.fixture(scope="session")
def report(sales):
    rows, cleaning = sales
    return build_report(
        rows,
        cleaning,
        source=config.DATA_PATH.name,
        min_base_idr=config.MIN_BASE_SALES_IDR,
        weak_count=config.WEAK_OUTLET_COUNT,
    )

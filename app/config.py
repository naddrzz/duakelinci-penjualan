"""Runtime settings. Business thresholds are documented in docs/metrics.md."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = Path(
    os.environ.get("DATA_PATH", ROOT / "data" / "dua_kelinci_sample_sales_sep_oct_2026.csv")
)

# An outlet must have sold at least this much (net, IDR) in the base month to be
# ranked as "weakest". Filters out tiny outlets whose % change is noise.
MIN_BASE_SALES_IDR = 5_000_000

# How many weakest outlets to flag.
WEAK_OUTLET_COUNT = 5

# Maximum size accepted by POST /api/upload (10 MiB).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

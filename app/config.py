"""Runtime settings. Business thresholds are documented in docs/metrics.md."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = Path(
    os.environ.get("DATA_PATH", ROOT / "data" / "dua_kelinci_sample_sales_sep_oct_2026.csv")
)

# Note: By default at runtime (`min_base_idr=None` in `build_report`), the base-month
# materiality floor is derived directly as the exact unrounded 1st quartile (Q1 / P25)
# of active base-month outlets (`Rp 4.927.700` on the bundled sample CSV).
# How many weakest outlets to flag.
WEAK_OUTLET_COUNT = 5

# Maximum size accepted by POST /api/upload (10 MiB).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

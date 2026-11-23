FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

RUN useradd --no-log-init --create-home --uid 10001 appuser \
    && chmod -R a+rX /app

USER appuser

# Build-time self-check: fail the image build immediately if any self-hosted font,
# OFL licence, logo, favicon, stylesheet, script, template, or CSV dataset is missing or unreadable by appuser.
RUN python -c "\
from pathlib import Path; \
from app.config import DATA_PATH; \
from app.data import load_sales; \
from app.analysis import build_report; \
checks = { \
    'app/static/fonts/InterVariable.woff2': b'wOF2', \
    'app/static/fonts/MontserratVariable.woff2': b'wOF2', \
    'app/static/fonts/LICENSE-Inter.txt': b'', \
    'app/static/fonts/LICENSE-Montserrat.txt': b'', \
    'app/static/logo-dk.png': b'\\x89PNG\\r\\n\\x1a\\n', \
    'app/static/favicon.ico': b'\\x00\\x00\\x01\\x00', \
    'app/static/favicon.png': b'\\x89PNG\\r\\n\\x1a\\n', \
    'app/static/apple-touch-icon.png': b'\\x89PNG\\r\\n\\x1a\\n', \
    'app/static/app.css': b'', \
    'app/static/app.js': b'', \
    'app/templates/base.html': b'', \
    'app/templates/_macros.html': b'', \
    'app/templates/ringkasan.html': b'', \
    'app/templates/wilayah_merek.html': b'', \
    'app/templates/outlet_terlemah.html': b'', \
}; \
missing = [p for p, sig in checks.items() if not Path(p).is_file() or Path(p).stat().st_size == 0 or not Path(p).read_bytes().startswith(sig)]; \
assert not missing, f'Missing or corrupt bundled assets: {missing}'; \
rows, cleaning = load_sales(DATA_PATH); \
report = build_report(rows, cleaning, source=DATA_PATH.name); \
assert report['totals']['outlets'] > 0 \
"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/healthz', timeout=2)"]

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]

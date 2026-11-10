FROM python:3.11-slim

WORKDIR /app

# System dependencies (OpenCV runtime libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch index for the pinned +cpu builds in requirements.txt
ENV PIP_NO_CACHE_DIR=1 \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# Python dependencies first for layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code + trained weights + SPA build + benchmark samples
# frontend/dist-cloud is produced by: npm run build:cloud (same-origin API URLs)
COPY backend/ ./backend/
COPY tests/sample_scans/ ./tests/sample_scans/
COPY frontend/dist-cloud/ ./frontend/dist/

# Pre-download the embedding model so first request isn't slow
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || true

# HF Spaces expects the app on port 7860 (configurable via README front matter)
ENV PORT=7860
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/api/v1/health', timeout=5)" || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
# One public origin; API listens only on loopback. No source .env is copied.
FROM node:22-bookworm-slim AS web
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1 BUILD_STANDALONE=true API_PROXY_TARGET=http://127.0.0.1:8000
RUN npm run build -- --webpack

FROM node:22-bookworm-slim AS ocr
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libgomp1 ca-certificates tesseract-ocr && rm -rf /var/lib/apt/lists/*
COPY --from=web /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY backend/ backend/
COPY scripts/ scripts/
COPY fixtures/ fixtures/
COPY --from=web /build/frontend/.next/standalone/ frontend/
COPY --from=web /build/frontend/.next/static/ frontend/.next/static/
# OCR is invoked separately from Python and isn't found by Next output tracing.
COPY --from=ocr /build/node_modules/ frontend/node_modules/
RUN pip install --no-cache-dir -r backend/requirements.lock.txt && pip install --no-cache-dir --no-deps -e backend && python scripts/setup_ocr.py
EXPOSE 10000
CMD ["python", "scripts/cloud_start.py"]

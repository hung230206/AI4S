FROM node:22-bookworm-slim AS ocr
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --omit=dev

FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=ocr /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY backend/ backend/
COPY scripts/ scripts/
COPY fixtures/ fixtures/
COPY --from=ocr /build/node_modules frontend/node_modules/
RUN pip install --no-cache-dir -r backend/requirements.lock.txt && pip install --no-cache-dir -e backend && python scripts/setup_ocr.py
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m app.seed && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]

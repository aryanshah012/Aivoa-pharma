# Stage 1: Build Frontend (Vite + React)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Backend (FastAPI) + Static Frontend Assets
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
# Copy sample data for seeding
COPY sample_data/ ./sample_data/
# Copy compiled frontend into static directory for FastAPI SPA serving
COPY --from=frontend-builder /app/frontend/dist ./static

EXPOSE 8000

CMD ["sh", "-c", "python -m app.db.init_db && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

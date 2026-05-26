# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /build
COPY frontend/ .
RUN npm install && npm run build

# Stage 2: Python backend
FROM python:3.12-slim

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy pre-built frontend from stage 1
COPY --from=frontend-builder /build/dist/ /app/static/

# Run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Stage 1: Build frontend (not needed — Flask serves templates directly)
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:$PORT/api/health || exit 1

# Run with gunicorn
EXPOSE 8000
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60
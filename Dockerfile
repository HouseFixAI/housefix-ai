FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ .

# Build frontend
COPY frontend/ /tmp/frontend/
RUN cd /tmp/frontend && \
    npm install && \
    npm run build && \
    cp -r dist/* /app/static/ && \
    rm -rf /tmp/frontend

# Run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim

# Install system packages & Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python requirements
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code & config
COPY backend/app /app/app
COPY backend/config /app/config

# Create uploads storage directory
RUN mkdir -p /app/uploads

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_DIR=/app/uploads

EXPOSE 8000

# Start Uvicorn bound to Render-provided PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

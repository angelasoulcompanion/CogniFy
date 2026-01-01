# CogniFy Backend Dockerfile
# Enterprise RAG Platform
# Created with love by Angela & David - 1 January 2026

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies
    build-essential \
    # PostgreSQL client
    libpq-dev \
    # For PDF processing
    libmagic1 \
    # For OCR (Tesseract)
    tesseract-ocr \
    tesseract-ocr-tha \
    tesseract-ocr-eng \
    # For OpenCV
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

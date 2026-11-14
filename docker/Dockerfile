# Multi-stage build for production
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt


# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY configs/ ./configs/

# Make sure scripts and user binaries are in PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check using Python stdlib urllib
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/liveness')"

# Run application with multiple workers for production
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

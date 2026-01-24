# =============================================================================
# Agent Twitter - Backend Dockerfile
# Multi-stage build for optimal image size
# =============================================================================

FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Final stage
# =============================================================================
FROM python:3.12-slim

# Set labels
LABEL maintainer="Agent Twitter Contributors"
LABEL description="Agent Twitter Backend - FastAPI with AI agent orchestration"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY *.py ./
COPY services/ ./services/
COPY store.py ./
COPY orchestrator.py ./
COPY agents.json ./

# Create directory for uploaded files
RUN mkdir -p /app/uploads

# Set environment defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000

# Expose port
EXPOSE 8000

# Health check (use PORT if set)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c "curl -f http://localhost:${PORT:-8000}/health || exit 1"

# Run the application (respect PORT if provided)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

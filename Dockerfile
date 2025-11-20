# Stage 1: Builder - Install dependencies with build tools
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies only
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    python3-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt pyproject.toml poetry.lock* ./

# Install dependencies to user directory (sẽ copy sang stage 2)
RUN --mount=type=cache,target=/root/.cache/pip \
    echo "Installing dependencies from requirements.txt..." && \
    pip install --user -r requirements.txt && \
    echo "✓ All dependencies installed successfully"

# Stage 2: Runtime - Chỉ có runtime dependencies, không có build tools
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/root/.local/bin:$PATH

# Install only runtime dependencies (không có build tools)
RUN apt-get update && apt-get install -y \
    # OpenCV dependencies (for image processing)
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # PostgreSQL runtime (không có -dev)
    libpq5 \
    # Utilities
    wget \
    curl \
    # gosu for switching users in entrypoint
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Verify key dependencies are installed
RUN echo "Verifying key dependencies..." && \
    python -c "import torch; import transformers; import PIL; print('✓ Core dependencies imported successfully')" && \
    echo "✓ All dependencies verified successfully"

# Copy application code
# Note: If model is trained before build, it will be included in the image
# However, docker-compose.yml uses volume mount for ./data/models, so
# the model from host will override the one in image (allows model updates without rebuild)
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# Keep as root for entrypoint to fix permissions
# Will switch to app user in entrypoint script
# USER app

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/hello-world')" || exit 1

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

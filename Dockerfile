FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y \
    # OpenCV and PaddleOCR dependencies
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    # Additional dependencies for PaddleOCR (from GitHub issues)
    libssl-dev \
    cmake \
    # PostgreSQL build dependencies
    libpq-dev \
    # Build tools
    gcc \
    g++ \
    make \
    pkg-config \
    python3-dev \
    libffi-dev \
    # Pillow build dependencies
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    # Utilities
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml poetry.lock* ./

# Install numpy first with version constraint (must be < 2.0 for PaddleOCR)
# This ensures numpy is installed before PaddlePaddle/PaddleOCR
RUN pip install --no-cache-dir "numpy<2.0.0,>=1.21.0"

# Create requirements without PaddleOCR, PaddlePaddle and numpy (numpy already installed)
# PaddlePaddle and PaddleOCR will be installed from official source separately
RUN grep -v "paddleocr" requirements.txt > /tmp/requirements_no_paddleocr.txt || true
RUN grep -v "paddlepaddle" /tmp/requirements_no_paddleocr.txt > /tmp/requirements_no_paddleocr_no_paddle.txt || true
RUN grep -v "numpy" /tmp/requirements_no_paddleocr_no_paddle.txt > /tmp/requirements_clean.txt || true

# Install dependencies first (without PaddleOCR, PaddlePaddle and numpy)
RUN pip install --no-cache-dir -r /tmp/requirements_clean.txt

# ============================================
# Install PaddlePaddle FIRST (theo README)
# ============================================
# README: "Install PaddlePaddle refer to Installation Guide, after then, install the PaddleOCR toolkit"
RUN echo "Step 1: Installing PaddlePaddle (CPU version)..." && \
    pip install --no-cache-dir paddlepaddle==2.6.2 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/ && \
    python -c "import paddle; print(f'✓ PaddlePaddle {paddle.__version__} installed successfully')" || \
    (echo "WARNING: Official source failed, trying PyPI..." && \
     pip install --no-cache-dir paddlepaddle==2.6.2 && \
     python -c "import paddle; print(f'✓ PaddlePaddle {paddle.__version__} installed from PyPI')" || \
     (echo "FATAL ERROR: PaddlePaddle installation failed!" && exit 1))

# ============================================
# Install PaddleOCR AFTER PaddlePaddle (theo README)
# ============================================
# README: "python -m pip install paddleocr" (basic text recognition)
# Skip PyMuPDF (optional dependency for PDF) - chỉ cần OCR từ ảnh
RUN echo "Step 2: Installing PaddleOCR (after PaddlePaddle, skipping PyMuPDF)..." && \
    pip install --no-cache-dir paddleocr==2.7.0 --no-deps && \
    pip install --no-cache-dir pyclipper shapely scipy lmdb "opencv-python>=4.5.0,<4.7.0" pillow "numpy<2.0.0" scikit-image imgaug visualdl tqdm python-docx rapidfuzz && \
    python -c "from paddleocr import PaddleOCR; print('✓ PaddleOCR installed successfully (without PyMuPDF)')" || \
    (echo "FATAL ERROR: PaddleOCR installation failed!" && exit 1)

# ============================================
# Verify PaddleOCR can be imported (lightweight check)
# ============================================
# Chỉ verify import, không khởi tạo full OCR trong build (tránh segmentation fault)
RUN echo "Step 3: Verifying PaddleOCR import..." && \
    python -c "import paddle; from paddleocr import PaddleOCR; print('✓ PaddleOCR and PaddlePaddle imported successfully')" || \
    (echo "ERROR: PaddleOCR or PaddlePaddle import failed!" && exit 1)

# ============================================
# Note: Models will be downloaded on first use
# ============================================
# Không pre-download models trong build để tránh segmentation fault
# Models sẽ được download tự động khi app chạy lần đầu
RUN echo "Step 4: Skipping model pre-download (will download on first use to avoid build issues)"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/hello-world')" || exit 1

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 5000"]

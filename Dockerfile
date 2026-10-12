# Redragon Controller - Multi-stage Docker Build
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libusb-1.0-0-dev \
    libhidapi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --user -e ".[dev]"

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0-0 \
    libhidapi-hidraw0 \
    libhidapi-libusb0 \
    udev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r redragon && useradd -r -g redragon -G plugdev redragon

# Copy Python packages from builder
COPY --from=builder /root/.local /home/redragon/.local

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir --user -e .

# Set up udev rules for HID device access
COPY config/99-redragon.rules /etc/udev/rules.d/99-redragon.rules

# Environment
ENV PATH="/home/redragon/.local/bin:${PATH}"
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Switch to non-root user
USER redragon

# Default command
ENTRYPOINT ["redragon"]
CMD ["--help"]
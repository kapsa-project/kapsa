# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies to /opt/venv
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first (using 'kapsa' as username since 'operator' group already exists in base image)
RUN groupadd -g 1000 kapsa && \
    useradd -m -u 1000 -g kapsa kapsa

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code and set ownership
COPY --chown=kapsa:kapsa src/ ./src/
COPY --chown=kapsa:kapsa setup.py .

# Install the package in the venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER kapsa

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the operator
CMD ["kopf", "run", "--all-namespaces", "/app/src/kapsa/main.py"]

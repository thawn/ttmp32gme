# Use modern Python 3.12 slim image as base
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies (wget, unzip for downloads, ffmpeg for audio conversion, git for setuptools-scm, chromium for PDF generation)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        unzip \
        xz-utils \
        ca-certificates \
        ffmpeg \
        git \
        chromium \
        chromium-sandbox && \
    # Update CA certificates to fix certificate issues
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install uv for faster, more reliable package management
# Using the official installation method for containers
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install tttool (from releases)
# Note: --no-check-certificate is required in some build environments due to SSL certificate chain issues.
# This is a known issue with intermediate certificates in Docker builds.
# For production builds with proper certificate setup, this flag can be removed.
RUN TTTOOL_VERSION="1.8.1" && \
    wget --no-check-certificate "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip" && \
    unzip -o -q "tttool-${TTTOOL_VERSION}.zip" && \
    chmod +x tttool && \
    mv tttool /usr/local/bin/ && \
    rm "tttool-${TTTOOL_VERSION}.zip"

# Copy application source
COPY . /app/

# Install Python dependencies using uv
# Using --native-tls to avoid certificate issues in containers
RUN uv pip install --system --no-cache --native-tls -e .

# Test stage - runs unit and integration tests
FROM base AS test

# Install test dependencies using uv
RUN uv pip install --system --no-cache --native-tls -e ".[test]"

# Run tests
RUN pytest tests/unit/ -v --tb=short

# Production stage - final image
FROM base AS production

# Create a non-root user for running the application
# Using UID/GID 1000 which is common for the first user on most Linux systems
# This allows for better compatibility with Podman's user namespace mapping
RUN groupadd -g 1000 ttmp32gme && \
    useradd -r -u 1000 -g ttmp32gme -m -d /home/ttmp32gme -s /bin/bash ttmp32gme

# Copy and set up entrypoint script
COPY resources/build_assets/docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set up directories and copy config
# Use proper permissions instead of 777 for security
RUN mkdir -p /data/library /mnt/tiptoi && \
    cp /app/src/ttmp32gme/config.sqlite /data/ && \
    chown -R ttmp32gme:ttmp32gme /data /mnt/tiptoi && \
    chmod -R 775 /data && \
    chmod 664 /data/config.sqlite

# Declare volumes for persistent data
# This helps Podman/Docker users understand which directories should be mounted
VOLUME ["/data", "/mnt/tiptoi"]

# Expose port 8080
EXPOSE 8080

# Switch to non-root user
USER ttmp32gme

# Run the Python backend with entrypoint script
# Using ENTRYPOINT allows passing additional arguments to docker run
# e.g., docker run thawn/ttmp32gme -vv
# The entrypoint script combines defaults with user arguments
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Optional health check
HEALTHCHECK --interval=5m --timeout=3s \
    CMD wget -q --spider http://localhost:8080/ || exit 1

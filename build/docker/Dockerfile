# Use modern Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (wget, unzip for downloads, ffmpeg for audio conversion, git for setuptools-scm)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        unzip \
        xz-utils \
        ca-certificates \
        ffmpeg \
        git && \
    rm -rf /var/lib/apt/lists/*

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

# Install Python dependencies
# Note: --trusted-host flags are required in some build environments due to SSL certificate chain issues.
# This is a known issue with intermediate certificates in Docker builds.
# For production builds with proper certificate setup, these flags can be removed.
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -e .

# Create a non-root user for running the application
# Using UID/GID 1000 which is common for the first user on most Linux systems
# This allows for better compatibility with Podman's user namespace mapping
RUN groupadd -g 1000 ttmp32gme && \
    useradd -r -u 1000 -g ttmp32gme -m -d /home/ttmp32gme -s /bin/bash ttmp32gme

# Set up directories and copy config
# Use proper permissions instead of 777 for security
ENV APPDATA=/var/lib/
RUN mkdir -p ${APPDATA}/ttmp32gme/library /mnt/tiptoi && \
    cp /app/src/ttmp32gme/config.sqlite ${APPDATA}/ttmp32gme/ && \
    chown -R ttmp32gme:ttmp32gme ${APPDATA}/ttmp32gme /mnt/tiptoi && \
    chmod -R 775 ${APPDATA}/ttmp32gme && \
    chmod 664 ${APPDATA}/ttmp32gme/config.sqlite

# Declare volumes for persistent data
# This helps Podman/Docker users understand which directories should be mounted
VOLUME ["${APPDATA}/ttmp32gme", "/mnt/tiptoi"]

# Expose port 8080
EXPOSE 8080

# Switch to non-root user
USER ttmp32gme

# Run the Python backend
CMD ["python", "-m", "ttmp32gme.ttmp32gme", "--host=0.0.0.0", "--port=8080", "--database=/var/lib/ttmp32gme/config.sqlite", "--library=/var/lib/ttmp32gme/library"]

# Optional health check
HEALTHCHECK --interval=5m --timeout=3s \
    CMD wget -q --spider http://localhost:8080/ || exit 1

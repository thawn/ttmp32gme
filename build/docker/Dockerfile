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

# Set up directories and copy config
ENV APPDATA=/var/lib/
RUN mkdir -p ${APPDATA}/ttmp32gme/library /mnt/tiptoi && \
    cp /app/src/ttmp32gme/config.sqlite ${APPDATA}/ttmp32gme/ && \
    chmod -R 777 ${APPDATA}/ttmp32gme/library

# Expose port 8080
EXPOSE 8080

# Run the Python backend
CMD ["python", "-m", "ttmp32gme.ttmp32gme", "--host=0.0.0.0", "--port=8080", "--database=/var/lib/ttmp32gme/config.sqlite", "--library=/var/lib/ttmp32gme/library"]

# Optional health check
HEALTHCHECK --interval=5m --timeout=3s \
    CMD wget -q --spider http://localhost:8080/ || exit 1

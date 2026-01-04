#!/bin/sh
# Docker entrypoint script for ttmp32gme
# Combines default arguments with user-provided arguments

# Default arguments that should always be set for Docker environment
exec python -m ttmp32gme.ttmp32gme \
    --host=0.0.0.0 \
    --port=8080 \
    --database=/data/config.sqlite \
    --library=/data/library \
    "$@"

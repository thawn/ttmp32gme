#!/bin/sh
# Docker entrypoint script for ttmp32gme
# Combines default arguments with user-provided arguments
# Supports environment variables for configuration

# Build arguments array from environment variables and defaults
ARGS=""

# Host (default: 0.0.0.0, can be overridden by TTMP32GME_HOST)
ARGS="$ARGS --host=${TTMP32GME_HOST:-0.0.0.0}"

# Port (default: 8080, can be overridden by TTMP32GME_PORT)
ARGS="$ARGS --port=${TTMP32GME_PORT:-8080}"

# Database path (default: /data/config.sqlite, can be overridden by TTMP32GME_DATABASE)
ARGS="$ARGS --database=${TTMP32GME_DATABASE:-/data/config.sqlite}"

# Library path (default: /data/library, can be overridden by TTMP32GME_LIBRARY)
ARGS="$ARGS --library=${TTMP32GME_LIBRARY:-/data/library}"

# Verbosity (if TTMP32GME_VERBOSE is set)
if [ -n "$TTMP32GME_VERBOSE" ]; then
    case "$TTMP32GME_VERBOSE" in
        1|v|info|INFO)
            ARGS="$ARGS -v"
            ;;
        2|vv|debug|DEBUG)
            ARGS="$ARGS -vv"
            ;;
    esac
fi

# No browser flag (if TTMP32GME_NO_BROWSER is set)
if [ "$TTMP32GME_NO_BROWSER" = "true" ] || [ "$TTMP32GME_NO_BROWSER" = "1" ]; then
    ARGS="$ARGS --no-browser"
fi

# Dev mode (if TTMP32GME_DEV is set)
if [ "$TTMP32GME_DEV" = "true" ] || [ "$TTMP32GME_DEV" = "1" ]; then
    ARGS="$ARGS --dev"
fi

# Execute with environment-based args + user command line args
# User args come last so they can override environment variables
exec python -m ttmp32gme.ttmp32gme $ARGS "$@"

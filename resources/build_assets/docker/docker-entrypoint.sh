#!/bin/sh
# Docker entrypoint script for ttmp32gme
# Combines default arguments with user-provided arguments
# Supports environment variables for configuration

# Note: This script uses word splitting intentionally. Paths with spaces should be
# passed via command line arguments instead of environment variables if needed.

# Build arguments from environment variables and defaults
ARGS=""
ARGS="$ARGS --host=${TTMP32GME_HOST:-0.0.0.0}"
ARGS="$ARGS --port=${TTMP32GME_PORT:-8080}"
ARGS="$ARGS --database=${TTMP32GME_DATABASE:-/data/config.sqlite}"
ARGS="$ARGS --library=${TTMP32GME_LIBRARY:-/data/library}"

# Add verbosity if set
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

# Add no-browser flag if set
if [ "$TTMP32GME_NO_BROWSER" = "true" ] || [ "$TTMP32GME_NO_BROWSER" = "1" ]; then
    ARGS="$ARGS --no-browser"
fi

# Add dev mode if set
if [ "$TTMP32GME_DEV" = "true" ] || [ "$TTMP32GME_DEV" = "1" ]; then
    ARGS="$ARGS --dev"
fi

# Execute with environment-based args first, then user command line args
# shellcheck disable=SC2086
# (Word splitting is intentional here to expand ARGS into separate arguments)
exec python -m ttmp32gme.ttmp32gme $ARGS "$@"

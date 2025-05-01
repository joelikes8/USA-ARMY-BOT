#!/usr/bin/env bash

# Build script for Render USA Army application
set -o errexit

echo "Starting USA Army application build..."

# Install Python dependencies
pip install -r requirements_for_render.txt

# Log service configuration
echo "Service configuration:"
echo "- PORT: $PORT"
echo "- RUN_BOT: $RUN_BOT"
echo "- Python version: $(python --version)"

echo "==> USA Army combined service build completed successfully."
echo "==> This single web service will run both the Discord bot and web dashboard."

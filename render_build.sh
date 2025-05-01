#!/usr/bin/env bash

# This script runs during the build phase on Render

# Exit on error
set -o errexit

echo "Starting build process..."

# Install Python dependencies from requirements
pip install -r requirements_for_render.txt

# Log service configuration
if [ -n "$WORKER_MODE" ]; then
  echo "Service running in WORKER mode (no port binding needed)"
fi

if [ -n "$WEB_SERVICE_MODE" ]; then
  echo "Service running in WEB mode with custom port: $PORT"
  echo "Web service type: $WEB_SERVICE_MODE"
  echo "Application will bind to 0.0.0.0:$PORT"
fi

# Log successful build
echo "PORT is set to: $PORT"
echo "Build completed successfully."
echo "Python version: $(python --version)"

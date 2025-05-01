#!/usr/bin/env bash

# This script runs during the build phase on Render

# Exit on error
set -o errexit

echo "Starting build process..."

# Install Python dependencies from requirements
pip install -r requirements_for_render.txt

# Log successful build
echo "PORT is set to: $PORT"
echo "Build completed successfully."
echo "RENDER DISCOVERY: Port detection can be disabled with environment variables."

# Print port binding information for debugging
echo "Application will bind to 0.0.0.0:$PORT"

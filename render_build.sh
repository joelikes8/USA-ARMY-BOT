#!/usr/bin/env bash

# Simple build script for Render
set -o errexit

echo "Starting USA Army application build..."

# Install Python dependencies
pip install -r requirements_for_render.txt

# Print build info
echo "Python version: $(python --version)"
echo "Build completed successfully."

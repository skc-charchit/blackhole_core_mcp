#!/bin/bash

# Create dist directory
mkdir -p dist

# Copy static files to dist
cp -r public/* dist/

# Install dependencies
pip install -r requirements-netlify.txt

echo "Build completed successfully!"

#!/usr/bin/env bash
# build.sh
# This script builds the unified Monolith application on Render.com

set -e

echo "Building React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Installing Python Backend Requirements..."
cd backend
pip install -r requirements.txt
echo "Build Complete!"

#!/bin/bash
set -e

cd "$(dirname "$0")"

# Backend dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -e backend/[dev]

# AI module dependencies
pip install -r ai/requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..

echo "Setup complete!"

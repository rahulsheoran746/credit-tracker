#!/bin/bash
set -e

echo "==> Running tests..."
source venv/bin/activate
pip install -r requirements-dev.txt -q
pytest -v

echo ""
echo "==> Tests passed. Deploying..."
docker-compose up -d --build

echo ""
echo "==> Deployment complete. App running at http://localhost:8000"

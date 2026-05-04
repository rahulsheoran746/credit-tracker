#!/usr/bin/env bash
# One-command deploy for the Shiv Dairy production VM.
#
# Pulls latest code from GitHub for both repos, rebuilds containers,
# and restarts only the services whose images actually changed.
#
# Usage:  ./deploy.sh           (deploy everything)
#         ./deploy.sh app       (deploy only the backend)
#         ./deploy.sh frontend  (deploy only the frontend)
#
# Pre-reqs: both repos cloned side-by-side (~/credit-tracker, ~/credit-tracker-frontend)

set -euo pipefail

BACKEND_DIR="$HOME/credit-tracker"
FRONTEND_DIR="$HOME/credit-tracker-frontend"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.prod.yaml"

TARGET="${1:-all}"

green() { printf "\n\033[1;32m==>\033[0m %s\n" "$*"; }
red()   { printf "\n\033[1;31m!!\033[0m %s\n" "$*"; }

cd "$BACKEND_DIR"

# ── Pull latest ──────────────────────────────────────────────
if [ "$TARGET" = "all" ] || [ "$TARGET" = "app" ]; then
    green "Pulling backend..."
    git -C "$BACKEND_DIR" pull --ff-only
fi
if [ "$TARGET" = "all" ] || [ "$TARGET" = "frontend" ]; then
    green "Pulling frontend..."
    git -C "$FRONTEND_DIR" pull --ff-only
fi

# ── Rebuild + restart ───────────────────────────────────────
if [ "$TARGET" = "all" ]; then
    green "Rebuilding and restarting all services..."
    docker compose -f "$COMPOSE_FILE" up -d --build
elif [ "$TARGET" = "app" ]; then
    green "Rebuilding backend only..."
    docker compose -f "$COMPOSE_FILE" up -d --build app
elif [ "$TARGET" = "frontend" ]; then
    green "Rebuilding frontend only..."
    docker compose -f "$COMPOSE_FILE" up -d --build frontend
else
    red "Unknown target: $TARGET (use 'all', 'app', or 'frontend')"
    exit 1
fi

# ── Sanity check ────────────────────────────────────────────
green "Waiting 5s for services to settle..."
sleep 5

if docker compose -f "$COMPOSE_FILE" ps --format "{{.State}}" | grep -qE "^(exited|restarting)$"; then
    red "One or more services failed to start. Inspect with:"
    echo "   docker compose -f docker-compose.prod.yaml ps"
    echo "   docker compose -f docker-compose.prod.yaml logs --tail 50"
    exit 1
fi

green "Deploy complete. Running:"
docker compose -f "$COMPOSE_FILE" ps

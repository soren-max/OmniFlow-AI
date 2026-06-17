#!/usr/bin/env bash
set -euo pipefail

# ContentOps Agent - Run Linters
# Usage: ./scripts/lint.sh [backend|frontend|all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-all}"

run_backend_lint() {
    echo "🔍 Running ruff on backend..."
    uv run ruff check apps/api/
}

run_frontend_lint() {
    echo "🔍 Running eslint on frontend..."
    cd apps/web
    pnpm lint
    cd "$PROJECT_DIR"
}

case "$TARGET" in
    backend)
        run_backend_lint
        ;;
    frontend)
        run_frontend_lint
        ;;
    all)
        run_backend_lint
        run_frontend_lint
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "✅ Lint passed!"

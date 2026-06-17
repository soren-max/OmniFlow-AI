#!/usr/bin/env bash
set -euo pipefail

# ContentOps Agent - Run Tests
# Usage: ./scripts/test.sh [backend|frontend|all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-all}"

run_backend_tests() {
    echo "🧪 Running backend tests..."
    uv run pytest apps/api/tests/ -v --tb=short
}

run_frontend_tests() {
    echo "🧪 Running frontend tests..."
    cd apps/web
    pnpm test
    cd "$PROJECT_DIR"
}

case "$TARGET" in
    backend)
        run_backend_tests
        ;;
    frontend)
        run_frontend_tests
        ;;
    all)
        run_backend_tests
        run_frontend_tests
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "✅ All tests passed!"

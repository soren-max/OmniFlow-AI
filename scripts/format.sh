#!/usr/bin/env bash
set -euo pipefail

# ContentOps Agent - Format Code
# Usage: ./scripts/format.sh [backend|frontend|all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-all}"

run_backend_format() {
    echo "🎨 Running ruff format on backend..."
    uv run ruff format apps/api/
}

run_frontend_format() {
    echo "🎨 Running prettier on frontend..."
    pnpm format
}

case "$TARGET" in
    backend)
        run_backend_format
        ;;
    frontend)
        run_frontend_format
        ;;
    all)
        run_backend_format
        run_frontend_format
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "✅ Formatting complete!"

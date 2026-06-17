#!/usr/bin/env bash
set -euo pipefail

# ContentOps Agent - Development Environment Setup
# Usage: ./scripts/dev.sh

echo "🚀 Starting ContentOps Agent development environment..."

# 1. Start Docker services (PostgreSQL + Redis)
echo "📦 Starting Docker services..."
make docker-up

# 2. Install Python dependencies
echo "🐍 Installing Python dependencies..."
make install

# 3. Run database migrations (future)
# echo "🗄️  Running database migrations..."
# make migrate

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Frontend:     http://localhost:3000"
echo ""
echo "   Run 'make dev-api' to start the backend server."
echo "   Run 'make dev-web' to start the frontend server."

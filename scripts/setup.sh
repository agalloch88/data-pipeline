#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🔧 Setting up data-pipeline project..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.13 -m venv .venv
fi

source .venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install --upgrade pip -q
pip install -e ".[dev]" -q

echo "📊 Installing dbt dependencies..."
cd dbt_project
dbt deps 2>/dev/null || echo "  (no dbt packages to install)"
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set environment variables (OURA_TOKEN, OPENWEATHERMAP_KEY, GITHUB_TOKEN)"
echo "  2. source .venv/bin/activate"
echo "  3. dagster dev -m pipeline_assets"
echo "  4. cd dbt_project && dbt run"

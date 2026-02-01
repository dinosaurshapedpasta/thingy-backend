#!/bin/bash

# Automated test runner script for thingy-backend

echo "========================================"
echo "  Thingy Backend - Automated Tests"
echo "========================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source .venv/bin/activate || {
        echo "❌ Failed to activate virtual environment"
        echo "Please run: python -m venv .venv && source .venv/bin/activate"
        exit 1
    }
fi

# Install/update test dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest httpx

# Remove old test database if it exists
if [ -f "test.db" ]; then
    echo "🗑️  Removing old test database..."
    rm test.db
fi

echo ""
echo "🧪 Running automated tests..."
echo ""

# Run tests with pytest
pytest test_endpoints.py -v --tb=short

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Exit code: $TEST_EXIT_CODE"
fi

# Clean up test database
if [ -f "test.db" ]; then
    rm test.db
fi

echo ""
echo "========================================"
exit $TEST_EXIT_CODE

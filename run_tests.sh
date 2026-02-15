#!/bin/bash
# Run tests per-file to avoid titanoboa caching bug
# When run together, some tests fail due to boa.BoaError caching issues

set -e

echo "=================================="
echo "Running vyper-agentic-payments tests"
echo "=================================="

PASS=0
FAIL=0
TOTAL=0

for f in tests/test_*.py; do
    echo ""
    echo ">>> Running: $f"
    echo "---"
    if python -m pytest "$f" -v --tb=short; then
        ((PASS++))
    else
        ((FAIL++))
        echo "⚠️  FAILED: $f"
    fi
    ((TOTAL++))
done

echo ""
echo "=================================="
echo "SUMMARY: $PASS/$TOTAL test files passed"
if [ $FAIL -gt 0 ]; then
    echo "❌ $FAIL file(s) had failures"
    exit 1
else
    echo "✅ All test files passed!"
    exit 0
fi

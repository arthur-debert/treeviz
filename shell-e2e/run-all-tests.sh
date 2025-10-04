#!/usr/bin/env bash

# Master test runner for all shell-based end-to-end tests
# Runs reliability and compatibility tests for treeviz adapters

set -euo pipefail

# Get the project root directory (parent of shell-e2e)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHELL_E2E_DIR="$PROJECT_ROOT/shell-e2e"

echo "🧪 treeviz End-to-End Test Suite"
echo "================================="
echo "Project root: $PROJECT_ROOT"
echo "Test directory: $SHELL_E2E_DIR"
echo

echo "Checking prerequisites..."
if ! command -v python &>/dev/null; then
	echo "❌ Python not found in PATH"
	exit 1
fi

if [[ ! -f "$PROJECT_ROOT/python/src/treeviz/__init__.py" ]]; then
	echo "❌ treeviz package not found at expected location"
	exit 1
fi

echo "✅ Prerequisites met"
echo

# Test 1: mdast Adapter Reliability
echo "Running Test 1: mdast Adapter Reliability..."
echo "============================================"
if "$SHELL_E2E_DIR/test-mdast-adapter-reliability.sh"; then
	echo "✅ Test 1 PASSED"
else
	echo "❌ Test 1 FAILED"
	exit 1
fi

echo
echo

# Test 2: Adapter Format Compatibility
echo "Running Test 2: Adapter Format Compatibility..."
echo "==============================================="
if "$SHELL_E2E_DIR/test-adapter-format-compatibility.sh"; then
	echo "✅ Test 2 PASSED"
else
	echo "❌ Test 2 FAILED"
	exit 1
fi

echo
echo

# Summary
echo "🎉 All End-to-End Tests Passed!"
echo "==============================="
echo "✅ mdast adapter handles CommonMark and GFM specs correctly"
echo "✅ YAML adapter format migration successful"
echo "✅ All built-in adapters function properly"
echo "✅ Icon mappings and field extractions working"
echo
echo "treeviz adapter reliability confirmed! 🚀"

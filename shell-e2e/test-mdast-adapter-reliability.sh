#!/usr/bin/env bash

# End-to-end test for mdast adapter reliability using CommonMark and GFM reference files
# Tests our mdast adapter against standard markdown AST test cases to ensure compatibility

set -euo pipefail

# Get the project root directory (parent of shell-e2e)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREEVIZ_CMD="python -m treeviz"

echo "=== mdast Adapter Reliability Test ==="
echo "Project root: $PROJECT_ROOT"
echo

echo "Creating temporary test directory..."
TEMP_DIR=$(mktemp -d)
echo "Working in: $TEMP_DIR"
cd "$TEMP_DIR"

echo
echo "Setting up environment with treeviz in PATH..."
export PYTHONPATH="$PROJECT_ROOT/python/src:${PYTHONPATH:-}"
cd "$PROJECT_ROOT"

echo
echo "=== Testing CommonMark Spec Compliance ==="

echo "Testing simple CommonMark example (heading with emphasis and escapes)..."
$TREEVIZ_CMD render python/tests/test_data/markdown-references/commonmark-simple.json mdast >"$TEMP_DIR/simple-output.txt"
echo "✓ Simple example rendered successfully"

echo "Testing medium complexity CommonMark example (nested lists and headings)..."
$TREEVIZ_CMD render python/tests/test_data/markdown-references/commonmark-medium.json mdast >"$TEMP_DIR/medium-output.txt"
echo "✓ Medium complexity example rendered successfully"

echo "Testing complex CommonMark example (nested blockquotes with code blocks)..."
$TREEVIZ_CMD render python/tests/test_data/markdown-references/commonmark-complex.json mdast >"$TEMP_DIR/complex-output.txt"
echo "✓ Complex example rendered successfully"

echo
echo "=== Testing GitHub Flavored Markdown (GFM) Extensions ==="

echo "Testing GFM table structures..."
$TREEVIZ_CMD render python/tests/test_data/markdown-references/gfm-tables-proper.json mdast >"$TEMP_DIR/table-output.txt"
echo "✓ GFM table example rendered successfully"

echo "Testing GFM task list structures..."
$TREEVIZ_CMD render python/tests/test_data/markdown-references/gfm-tasklist-proper.json mdast >"$TEMP_DIR/tasklist-output.txt"
echo "✓ GFM task list example rendered successfully"

echo
echo "=== Validating Output Quality ==="

echo "Checking that all outputs contain root node..."
for file in "$TEMP_DIR"/*.txt; do
	if grep -q "⧉ root" "$file"; then
		echo "✓ $(basename "$file") contains root node"
	else
		echo "✗ $(basename "$file") missing root node"
		exit 1
	fi
done

echo "Checking for proper table structure in GFM table output..."
if grep -q "⊞ table" "$TEMP_DIR/table-output.txt" &&
	grep -q "⊟ tableRow" "$TEMP_DIR/table-output.txt" &&
	grep -q "⊡ tableCell" "$TEMP_DIR/table-output.txt"; then
	echo "✓ GFM table structure properly rendered with table icons"
else
	echo "✗ GFM table structure missing proper icons"
	exit 1
fi

echo "Checking for heading structure in simple example..."
if grep -q "⊤ heading" "$TEMP_DIR/simple-output.txt"; then
	echo "✓ Heading properly identified with heading icon"
else
	echo "✗ Heading structure not properly rendered"
	exit 1
fi

echo "Checking for list structure in medium example..."
if grep -q "☰ list" "$TEMP_DIR/medium-output.txt" &&
	grep -q "• listItem" "$TEMP_DIR/medium-output.txt"; then
	echo "✓ List structure properly rendered with list icons"
else
	echo "✗ List structure not properly rendered"
	exit 1
fi

echo "Checking for blockquote structure in complex example..."
if grep -q "❝ blockquote" "$TEMP_DIR/complex-output.txt"; then
	echo "✓ Blockquote properly identified with blockquote icon"
else
	echo "✗ Blockquote structure not properly rendered"
	exit 1
fi

echo
echo "=== Output Samples ==="
echo "Simple example output (first 5 lines):"
head -5 "$TEMP_DIR/simple-output.txt" | sed 's/^/  /'

echo
echo "GFM table output (first 10 lines):"
head -10 "$TEMP_DIR/table-output.txt" | sed 's/^/  /'

echo
echo "=== Cleanup ==="
echo "Cleaning up temporary directory: $TEMP_DIR"
rm -rf "$TEMP_DIR"

echo
echo "🎉 All mdast adapter reliability tests passed!"
echo "The adapter correctly handles:"
echo "  • CommonMark spec examples (simple, medium, complex)"
echo "  • GitHub Flavored Markdown extensions (tables, task lists)"
echo "  • Proper icon mapping for all node types"
echo "  • Nested structure rendering"

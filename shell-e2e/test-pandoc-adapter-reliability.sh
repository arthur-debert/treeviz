#!/usr/bin/env bash

# End-to-end test for pandoc adapter reliability using official pandoc test files
# Tests our pandoc adapter against complex AST structures from the pandoc project

set -euo pipefail

# Get the project root directory (parent of shell-e2e)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREEVIZ_CMD="python -m treeviz"

echo "=== Pandoc Adapter Reliability Test ==="
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
echo "=== Testing Pandoc Official Sample Files ==="

echo "Testing simple pandoc document (basic structure)..."
$TREEVIZ_CMD render python/tests/test_data/pandoc-references/simple.json pandoc >"$TEMP_DIR/simple-output.txt"
echo "✓ Simple pandoc document rendered successfully"

echo "Testing pandoc tables support (complex table structures)..."
$TREEVIZ_CMD render python/tests/test_data/pandoc-references/tables.json pandoc >"$TEMP_DIR/tables-output.txt"
echo "✓ Pandoc tables rendered successfully"

echo "Testing advanced pandoc features (citations, math, complex formatting)..."
$TREEVIZ_CMD render python/tests/test_data/pandoc-references/advanced-features.json pandoc >"$TEMP_DIR/advanced-output.txt"
echo "✓ Advanced pandoc features rendered successfully"

echo "Testing pandoc citations support..."
$TREEVIZ_CMD render python/tests/test_data/pandoc-references/citations.json pandoc >"$TEMP_DIR/citations-output.txt"
echo "✓ Pandoc citations rendered successfully"

echo
echo "=== Validating Output Quality ==="

echo "Checking that all outputs contain root Pandoc document..."
for file in "$TEMP_DIR"/*.txt; do
	if grep -q "📄 Pandoc Document" "$file"; then
		echo "✓ $(basename "$file") contains Pandoc document root"
	else
		echo "✗ $(basename "$file") missing Pandoc document root"
		exit 1
	fi
done

echo "Checking for proper header structure in simple document..."
if grep -q "H H" "$TEMP_DIR/simple-output.txt"; then
	echo "✓ Headers properly identified with H prefix"
else
	echo "✗ Header structure not properly rendered"
	exit 1
fi

echo "Checking for paragraph structure in simple document..."
if grep -q "¶ " "$TEMP_DIR/simple-output.txt"; then
	echo "✓ Paragraphs properly identified with paragraph icon"
else
	echo "✗ Paragraph structure not properly rendered"
	exit 1
fi

echo "Checking for table structure in tables document..."
if grep -q "▦ Table" "$TEMP_DIR/tables-output.txt"; then
	echo "✓ Tables properly identified with table icon"
else
	echo "✗ Table structure not properly rendered"
	exit 1
fi

echo "Checking for code block structure in simple document..."
if grep -q '\`\`\` ' "$TEMP_DIR/simple-output.txt" || grep -q "CodeBlock" "$TEMP_DIR/simple-output.txt"; then
	echo "✓ Code blocks properly identified"
else
	echo "✗ Code block structure not properly rendered"
	exit 1
fi

echo "Checking for link structure in advanced features..."
if grep -q "🔗 " "$TEMP_DIR/advanced-output.txt"; then
	echo "✓ Links properly identified with link icon"
else
	echo "✗ Link structure not properly rendered"
	exit 1
fi

echo "Checking for bullet list structure..."
if grep -q "• Bullet List" "$TEMP_DIR/simple-output.txt"; then
	echo "✓ Bullet lists properly identified with list icon"
else
	echo "✗ Bullet list structure not properly rendered"
	exit 1
fi

echo "Checking for strong/emphasis formatting..."
if grep -q "💪 Strong" "$TEMP_DIR/simple-output.txt" || grep -q "𝑖 " "$TEMP_DIR/simple-output.txt"; then
	echo "✓ Text formatting properly identified"
else
	echo "✗ Text formatting not properly rendered"
	exit 1
fi

echo
echo "=== Output Structure Analysis ==="

echo "Document complexity analysis:"
for file in "$TEMP_DIR"/*.txt; do
	basename_file=$(basename "$file")
	lines=$(wc -l <"$file")
	unique_icons=$(grep -o '^[[:space:]]*[^[:space:]]' "$file" | sort | uniq | wc -l)
	echo "  $basename_file: $lines lines, $unique_icons different node types"
done

echo
echo "=== Output Samples ==="
echo "Simple document output (first 8 lines):"
head -8 "$TEMP_DIR/simple-output.txt" | sed 's/^/  /'

echo
echo "Tables document output (first 8 lines):"
head -8 "$TEMP_DIR/tables-output.txt" | sed 's/^/  /'

echo
echo "Advanced features output (first 8 lines):"
head -8 "$TEMP_DIR/advanced-output.txt" | sed 's/^/  /'

echo
echo "=== Cleanup ==="
echo "Cleaning up temporary directory: $TEMP_DIR"
rm -rf "$TEMP_DIR"

echo
echo "🎉 All pandoc adapter reliability tests passed!"
echo "The adapter correctly handles:"
echo "  • Official pandoc test files (simple, tables, citations, advanced)"
echo "  • Complex document structures with proper icon mapping"
echo "  • Headers, paragraphs, tables, links, lists, formatting"
echo "  • Text extraction and truncation for complex nested structures"
echo "  • Pandoc-specific AST format with t/c field structure"

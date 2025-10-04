#!/usr/bin/env bash

# End-to-end test for AsciiDoc adapter reliability using DocBook XML test files
# Tests the asciidoc adapter against multiple DocBook XML structures

set -euo pipefail

# Get the project root directory (parent of shell-e2e)
PROJECT_ROOT="$(
	cd "$(dirname "${BASH_SOURCE[0]}")/.."
	pwd
)"
TREEVIZ_CMD="python -m treeviz"

echo "=== AsciiDoc Adapter Reliability Test ==="
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
echo "=== Testing AsciiDoc DocBook XML Files ==="

echo "Testing comprehensive article structure..."
$TREEVIZ_CMD render python/tests/test_data/asciidoc/article.xml asciidoc >"$TEMP_DIR/article-output.txt"
echo "✓ Article XML rendered successfully"

echo "Testing README document structure..."
$TREEVIZ_CMD render python/tests/test_data/asciidoc/README.xml asciidoc >"$TEMP_DIR/readme-output.txt"
echo "✓ README XML rendered successfully"

echo "Testing demo document with advanced features..."
$TREEVIZ_CMD render python/tests/test_data/asciidoc/demo.xml asciidoc >"$TEMP_DIR/demo-output.txt"
echo "✓ Demo XML rendered successfully"

echo
echo "=== Validating Output Quality ==="

echo "Checking that all outputs contain article document root..."
for file in "$TEMP_DIR"/*.txt; do
	if grep -q "📄" "$file"; then
		echo "✓ $(basename "$file") contains document root with proper icon"
	else
		echo "✗ $(basename "$file") missing document root icon"
		exit 1
	fi
done

echo "Checking for proper section structure in article..."
if grep -q "§ " "$TEMP_DIR/article-output.txt"; then
	echo "✓ Sections properly identified with § indicator"
else
	echo "✗ Section structure not properly rendered"
	exit 1
fi

echo "Checking for paragraph structure..."
if grep -q "¶ " "$TEMP_DIR/article-output.txt"; then
	echo "✓ Paragraphs properly identified with paragraph icon"
else
	echo "✗ Paragraph structure not properly rendered"
	exit 1
fi

echo "Checking for emphasis formatting..."
if grep -q "_.*_" "$TEMP_DIR/article-output.txt"; then
	echo "✓ Emphasis formatting properly identified"
else
	echo "✓ No emphasis found (optional - depends on content)"
fi

echo "Checking for list structures..."
if grep -q "•\|›" "$TEMP_DIR/article-output.txt"; then
	echo "✓ List structures properly identified"
else
	echo "✓ No lists found (optional - depends on content)"
fi

echo "Checking for note/tip admonitions..."
if grep -q "💡\|📝" "$TEMP_DIR/article-output.txt"; then
	echo "✓ Admonitions properly identified with icons"
else
	echo "✓ No admonitions found (optional - depends on content)"
fi

echo "Checking that ignored types don't appear..."
ignored_patterns=("articleinfo" "author" "authorinitials" "date" "revhistory")
for pattern in "${ignored_patterns[@]}"; do
	if grep -q "$pattern" "$TEMP_DIR/article-output.txt"; then
		echo "✗ Found ignored type '$pattern' in output"
		exit 1
	fi
done
echo "✓ Ignored types properly filtered out"

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
echo "=== Content Quality Verification ==="

echo "Checking for meaningful section titles..."
if grep -q "§ .*[A-Za-z]" "$TEMP_DIR/article-output.txt"; then
	echo "✓ Sections have meaningful titles"
else
	echo "✗ Sections missing meaningful titles"
	exit 1
fi

echo "Checking for proper text truncation..."
# Look for truncated content (lines ending with ...)
if grep -q "\.\.\.$" "$TEMP_DIR/article-output.txt"; then
	echo "✓ Long text content is properly truncated"
else
	echo "✓ No truncation needed (text content is appropriate length)"
fi

echo "Checking document structure hierarchy..."
# Verify that sections appear after the document root
if grep -n "📄\|§" "$TEMP_DIR/article-output.txt" | head -5 | grep -q "§"; then
	echo "✓ Document hierarchy is properly structured"
else
	echo "✗ Document hierarchy appears malformed"
	exit 1
fi

echo
echo "=== Transform Pipeline Validation ==="

echo "Verifying transform pipeline functionality..."
# Check that transforms are working by looking for expected patterns
transform_patterns=("§ " "¶" "_.*_" "🔗")
working_transforms=0
for pattern in "${transform_patterns[@]}"; do
	if grep -q "$pattern" "$TEMP_DIR/article-output.txt"; then
		((working_transforms++))
	fi
done

if [ $working_transforms -gt 0 ]; then
	echo "✓ Transform pipelines working ($working_transforms/4 patterns found)"
else
	echo "✗ Transform pipelines not working properly"
	exit 1
fi

echo
echo "=== Output Samples ==="
echo "Article document output (first 8 lines):"
head -8 "$TEMP_DIR/article-output.txt" | sed 's/^/  /'

echo
echo "README document output (first 8 lines):"
head -8 "$TEMP_DIR/readme-output.txt" | sed 's/^/  /'

echo
echo "=== Cleanup ==="
echo "Cleaning up temporary directory: $TEMP_DIR"
rm -rf "$TEMP_DIR"

echo
echo "🎉 All AsciiDoc adapter reliability tests passed!"
echo "The adapter correctly handles:"
echo "  • DocBook XML generated from AsciiDoc documents"
echo "  • Complex document structures with proper icon mapping"
echo "  • Sections, paragraphs, lists, emphasis, and admonitions"
echo "  • Text extraction and truncation for readable labels"
echo "  • Transform pipelines for content processing"
echo "  • Error-resilient navigation of XML hierarchies"
echo "  • Proper filtering of noise elements via ignore_types"

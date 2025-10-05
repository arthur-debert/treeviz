#!/usr/bin/env bash

# End-to-end test for MediaWiki adapter reliability

set -euo pipefail

# Get the project root directory (parent of shell-e2e)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TREEVIZ_CMD="python -m treeviz"

echo "=== MediaWiki Adapter Reliability Test ==="
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
echo "=== Testing MediaWiki Sample Files ==="

echo "Testing complex MediaWiki document 1 (links, formatting)..."
$TREEVIZ_CMD render python/tests/test_data/mediawiki/complex1.json mediawiki >"$TEMP_DIR/complex1-output.txt"
echo "✓ Complex document 1 rendered successfully"

echo "Testing complex MediaWiki document 2 (tables)..."
$TREEVIZ_CMD render python/tests/test_data/mediawiki/complex2.json mediawiki >"$TEMP_DIR/complex2-output.txt"
echo "✓ Complex document 2 rendered successfully"

echo "Testing complex MediaWiki document 3 (templates)..."
$TREEVIZ_CMD render python/tests/test_data/mediawiki/complex3.json mediawiki >"$TEMP_DIR/complex3-output.txt"
echo "✓ Complex document 3 rendered successfully"

echo "Testing complex MediaWiki document 4 (nested structures)..."
$TREEVIZ_CMD render python/tests/test_data/mediawiki/complex4.json mediawiki >"$TEMP_DIR/complex4-output.txt"
echo "✓ Complex document 4 rendered successfully"

echo
echo "=== Validating Output Quality ==="

echo "Checking that all outputs contain root MediaWiki document..."
for file in "$TEMP_DIR"/*.txt; do
    if grep -q "📄 MediaWiki Document" "$file"; then
        echo "✓ $(basename "$file") contains MediaWiki document root"
    else
        echo "✗ $(basename "$file") missing MediaWiki document root"
        exit 1
    fi
done

echo "Checking for proper header structure..."
if grep -q "H1: " "$TEMP_DIR/complex1-output.txt"; then
    echo "✓ Headers properly identified with H1 prefix"
else
    echo "✗ Header structure not properly rendered"
    exit 1
fi

echo "Checking for link structure..."
if grep -q "🔗 " "$TEMP_DIR/complex1-output.txt"; then
    echo "✓ Wikilinks properly identified with link icon"
else
    echo "✗ Wikilink structure not properly rendered"
    exit 1
fi

echo "Checking for table structure..."
if grep -q "<table>" "$TEMP_DIR/complex2-output.txt"; then
    echo "✓ Tables properly identified with <table> tag"
else
    echo "✗ Table structure not properly rendered"
    exit 1
fi

echo "Checking for template structure..."
if grep -q "{{ Infobox }}" "$TEMP_DIR/complex3-output.txt"; then
    echo "✓ Templates properly identified with {{...}} syntax"
else
    echo "✗ Template structure not properly rendered"
    exit 1
fi

echo "Checking for parameter structure..."
if grep -q "name = ..." "$TEMP_DIR/complex3-output.txt"; then
    echo "✓ Parameters properly identified"
else
    echo "✗ Parameter structure not properly rendered"
    exit 1
fi

echo
echo "=== Cleanup ==="
echo "Cleaning up temporary directory: $TEMP_DIR"
rm -rf "$TEMP_DIR"

echo
echo "🎉 All MediaWiki adapter reliability tests passed!"
echo "The adapter correctly handles:"
echo "  • Complex MediaWiki ASTs with various features"
echo "  • Headers, links, tables, templates, and formatting"
echo "  • Nested structures and proper icon mapping"
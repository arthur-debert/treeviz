#!/bin/bash
# Sync docs from source to package for distribution
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Syncing docs from $PROJECT_ROOT/docs/shell-help to package..."

# Remove old docs if they exist
rm -rf "$PROJECT_ROOT/python/src/treeviz/docs/shell-help"

# Copy fresh docs
cp -r "$PROJECT_ROOT/docs/shell-help" "$PROJECT_ROOT/python/src/treeviz/docs/"

echo "Done! Docs synced to package."

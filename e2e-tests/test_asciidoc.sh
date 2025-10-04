#!/bin/bash

# A simple end-to-end test for the asciidoc adapter.
# It runs 3viz on a test file and checks for expected output.

# Run the 3viz command and capture the output
output=$(poetry run 3viz python/tests/test_data/asciidoc/article.xml asciidoc)

# Check if the output contains the expected article title
if echo "$output" | grep -q "The Article Title"; then
  echo "E2E test passed: Found 'The Article Title' in the output."
  exit 0
else
  echo "E2E test failed: Did not find 'The Article Title' in the output."
  exit 1
fi
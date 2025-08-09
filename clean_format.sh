#!/bin/bash

# Clean and format Python files using autoflake, black, and flake8
# Usage:
#   ./clean_format.sh             # Clean & format all .py files in current directory recursively
#   ./clean_format.sh file.py     # Clean & format a single Python file

set -e  # Exit immediately if a command exits with a non-zero status

# Function to clean a single file
clean_file() {
    local file="$1"
    echo "Cleaning: $file"

    # Remove trailing whitespace
    sed -i 's/[ \t]*$//' "$file"

    # Remove unused imports
    autoflake --in-place --remove-all-unused-imports --remove-unused-variables "$file"

    # Sort imports
    isort "$file"

    # Format with black
    black --line-length 79 "$file"

    # Lint check (optional, doesn't modify)
    flake8 "$file" || true
}

if [ $# -eq 1 ]; then
    clean_file "$1"
else
    find . -type f -name "*.py" | while read -r file; do
        clean_file "$file"
    done
fi

echo "✅ Cleaning & formatting complete!"

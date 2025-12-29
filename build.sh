#!/bin/bash
# Build standalone executable with Nuitka

set -e  # Exit on error

echo "Building OrcaSlicer Filament Tool standalone executable..."

# Check if Nuitka is installed
if ! python -c "import nuitka" 2>/dev/null; then
    echo "Installing Nuitka..."
    pip install nuitka
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ orcaslicer-export.build/ orcaslicer-export.dist/

# Build with Nuitka
echo "Compiling with Nuitka..."
python -m nuitka \
    --standalone \
    --onefile \
    --output-filename=orcaslicer-export \
    --output-dir=dist \
    --include-package=src \
    --assume-yes-for-downloads \
    --remove-output \
    src/cli.py

echo ""
echo "✓ Build complete!"
echo "  Executable: dist/orcaslicer-export"
echo ""
echo "Test the executable:"
echo "  ./dist/orcaslicer-export --help"

#!/bin/bash
set -e

# === Clean previous builds ===
rm -rf dist build package
rm -f SecureVault-*-linux.tar.gz
mkdir -p dist

# === Install application dependencies ===
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# === Install build tool (Nuitka) ===
pip install nuitka

# === Build with Nuitka ===
python3 -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --follow-imports \
  --enable-plugin=pyside6 \
  --include-qt-plugins=sensible,imageformats,qml \
  --include-data-dir=src/assets=assets \
  --include-data-file=version.py=version.py \
  --output-dir=dist \
  src/main.py


# === Make executable permissions ===
chmod +x dist/main.dist/main.bin

# === Get version ===
VERSION=$(python3 -c "from version import __version__; print(__version__)")

# === Prepare package directory ===
echo "Preparing package..."
mkdir -p package/SecureVault-$VERSION
cp -r dist/main.dist/* package/SecureVault-$VERSION/
cp -r src/assets package/SecureVault-$VERSION/ || true
cp version.py package/SecureVault-$VERSION/ || true
cp -r installer package/SecureVault-$VERSION/
cp LICENSE package/SecureVault-$VERSION/
cp README.md package/SecureVault-$VERSION/

# === Create tarball ===
echo "Creating distribution tarball..."
tar -czf SecureVault-linux.tar.gz -C package SecureVault-$VERSION

echo
echo "✅ Linux build complete!"
echo "Created: SecureVault-linux.tar.gz"
echo "To install:"
echo "  1. tar -xzf SecureVault-linux.tar.gz"
echo "  2. cd SecureVault-$VERSION"
echo "  3. sudo ./installer/install.sh"
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$ROOT_DIR/.pyinstaller-cache}"

APP_NAME="PinShift"
# Qt and PyInstaller must see the same environment path when .venv is a symlink.
BUILD_PYTHON="$(python -c 'from pathlib import Path; import sys; print(Path(sys.prefix).resolve() / "bin" / Path(sys.executable).name)')"
"$BUILD_PYTHON" packaging/collect_licenses.py
"$BUILD_PYTHON" -m PyInstaller --clean --noconfirm PinShift.spec

codesign --force --sign - "dist/${APP_NAME}.app"
codesign --verify --deep --strict "dist/${APP_NAME}.app"

echo "Built dist/${APP_NAME}.app"

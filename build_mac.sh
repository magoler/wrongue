#!/bin/bash
# Build Wrongue.app, install it to /Applications and open it.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="$(command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3.10 || true)"
if [ -z "$PYTHON" ]; then
  echo "Python 3.10+ not found. Install it with:  brew install python" >&2
  exit 1
fi

echo "==> Setting up build environment with $PYTHON"
[ -d .venv-build ] || "$PYTHON" -m venv .venv-build
.venv-build/bin/pip install -q --upgrade pip
.venv-build/bin/pip install -q -r requirements.txt

echo "==> Running tests"
.venv-build/bin/python -m pytest -q

echo "==> Building Wrongue.app"
rm -rf build dist
.venv-build/bin/python setup.py py2app > build.log 2>&1 || { echo "Build failed, see build.log" >&2; exit 1; }

echo "==> Installing to /Applications"
pkill -f "/Applications/Wrongue.app/Contents/MacOS/Wrongue" 2>/dev/null || true
sleep 1
rm -rf /Applications/Wrongue.app
ditto dist/Wrongue.app /Applications/Wrongue.app
open /Applications/Wrongue.app

echo
echo "Done. Look for A⇄א in the menu bar."
echo "Now turn on Wrongue in System Settings → Privacy & Security → Accessibility and Input Monitoring,"
echo "then quit Wrongue from its menu and open it again."

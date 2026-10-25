#!/usr/bin/env bash
# Copy OptAgent at the commit used in the paper next to research/ (unmodified).
set -euo pipefail
COMMIT=b4d2d12ba0bd4971626844a5c2c84c56cad3fc2a
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
git clone --quiet https://github.com/BESTLabAtSU/OptAgent.git "$TMP/OptAgent"
git -C "$TMP/OptAgent" checkout --quiet "$COMMIT"
for p in src config bestopt card_generator.py API.py; do
  rm -rf "$ROOT/$p"; cp -R "$TMP/OptAgent/$p" "$ROOT/$p"
done
cp "$TMP/OptAgent/LICENSE" "$ROOT/OPTAGENT_LICENSE"
rm -rf "$TMP"
echo "OptAgent $COMMIT copied into $ROOT"

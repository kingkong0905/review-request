#!/usr/bin/env bash
set -euo pipefail

PYPROJECT="pyproject.toml"
INIT_FILE="src/review_request/__init__.py"

usage() {
    echo "Usage: $0 [major|minor|patch]"
    echo "  major  — bump X in X.y.z  (e.g. 1.2.3 → 2.0.0)"
    echo "  minor  — bump Y in x.Y.z  (e.g. 1.2.3 → 1.3.0)"
    echo "  patch  — bump Z in x.y.Z  (e.g. 1.2.3 → 1.2.4)  [default]"
    exit 1
}

BUMP="${1:-patch}"
[[ "$BUMP" =~ ^(major|minor|patch)$ ]] || usage

current=$(grep -m1 '^version = ' "$PYPROJECT" | sed 's/version = "\(.*\)"/\1/')
IFS='.' read -r major minor patch <<< "$current"

case "$BUMP" in
    major) major=$((major + 1)); minor=0; patch=0 ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    patch) patch=$((patch + 1)) ;;
esac

new="${major}.${minor}.${patch}"

sed -i.bak "s/^version = \"${current}\"/version = \"${new}\"/" "$PYPROJECT" && rm "${PYPROJECT}.bak"
sed -i.bak "s/__version__ = \"${current}\"/__version__ = \"${new}\"/" "$INIT_FILE" && rm "${INIT_FILE}.bak"

echo "Bumped ${current} → ${new}"

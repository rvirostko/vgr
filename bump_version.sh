#!/usr/bin/env bash
set -euo pipefail

VERSION_FILE="version.py"

BUMP_PART="${1:-rev}"

if [[ "$BUMP_PART" != "minor" && "$BUMP_PART" != "rev" ]]; then
    echo "Invalid argument: $BUMP_PART"
    echo "Must be one of: minor, rev"
    exit 1
fi

# Extract current version
VERSION_LINE=$(grep '^__version__' "$VERSION_FILE")
VERSION=$(echo "$VERSION_LINE" | sed -E 's/.*"([^"]+)".*/\1/')

IFS='.' read -r MAJOR MINOR REV <<< "$VERSION"

if [[ "$BUMP_PART" == "minor" ]]; then
    MINOR=$((MINOR + 1))
    REV=0
else
    REV=$((REV + 1))
fi

NEW_VERSION="${MAJOR}.${MINOR}.${REV}"
NEW_DATE=$(date +%Y-%m-%d)

sed -i '' -E "s/^(__version__[[:space:]]*=[[:space:]]*\").*(\".*)/\1${NEW_VERSION}\2/" "$VERSION_FILE"
sed -i '' -E "s/^(__version_date__[[:space:]]*=[[:space:]]*\").*(\".*)/\1${NEW_DATE}\2/" "$VERSION_FILE"

cat ${VERSION_FILE}

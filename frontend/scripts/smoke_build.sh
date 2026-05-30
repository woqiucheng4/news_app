#!/usr/bin/env bash
# Build NewsFlow mobile targets for release-readiness smoke checks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> flutter pub get"
flutter pub get

echo "==> flutter gen-l10n"
flutter gen-l10n

echo "==> flutter analyze"
flutter analyze

echo "==> flutter test"
flutter test

echo "==> flutter build apk --debug"
flutter build apk --debug

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "==> flutter build ios --simulator --no-codesign"
  flutter build ios --simulator --no-codesign
else
  echo "==> Skipping iOS build (requires macOS)"
fi

echo "Smoke build completed."

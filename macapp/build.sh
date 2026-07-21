#!/usr/bin/env bash
# Build Woven.app from the SPM executable + Support/ bundle pieces.
# Requires only the Xcode Command Line Tools (swift, codesign, ditto).
#
#   macapp/build.sh [version]           ad-hoc signed (default, for testing)
#   CODESIGN_IDENTITY="Developer ID Application: ..." macapp/build.sh 1.0.0
#                                       Developer ID + hardened runtime; then
#                                       notarize + staple (commands below).
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${1:-0.1.0}"
APP="dist/Woven.app"

swift build -c release

rm -rf dist
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp .build/release/WovenApp "$APP/Contents/MacOS/Woven"
sed "s/__VERSION__/$VERSION/g" Support/Info.plist > "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"
[ -f Support/AppIcon.icns ] && cp Support/AppIcon.icns "$APP/Contents/Resources/"
# Menu-bar template icon - the Woven logogram (1x + 2x), rendered from
# editor/favicon.svg. Template = alpha-only black; macOS tints it per theme.
cp Support/woven-mark-18.png Support/woven-mark-36.png "$APP/Contents/Resources/" 2>/dev/null || true

if [ -n "${CODESIGN_IDENTITY:-}" ]; then
  # Developer ID path: hardened runtime + secure timestamp, then notarize.
  codesign --force --options runtime --timestamp \
           --entitlements Support/Woven.entitlements \
           -s "$CODESIGN_IDENTITY" "$APP"
  echo "Signed with: $CODESIGN_IDENTITY"
  echo "Next (once an App Store Connect API key or keychain profile exists):"
  echo "  ditto -c -k --keepParent $APP dist/Woven-macos.zip"
  echo "  xcrun notarytool submit dist/Woven-macos.zip --keychain-profile woven --wait"
  echo "  xcrun stapler staple $APP   # then re-zip for distribution"
else
  codesign --force -s - "$APP"   # ad-hoc: testing / early distribution
fi

ditto -c -k --keepParent "$APP" dist/Woven-macos.zip
echo ""
echo "Built $APP (version $VERSION)"
echo "Release artifact: macapp/dist/Woven-macos.zip"

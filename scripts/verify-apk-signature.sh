#!/usr/bin/env bash
set -euo pipefail
APK="${1:?Usage: verify-apk-signature.sh path/to/app.apk}"
APKSIGNER="${APKSIGNER:-${ANDROID_HOME:-}/build-tools/36.0.0/apksigner}"
"$APKSIGNER" verify --verbose --print-certs "$APK"
sha256sum "$APK"

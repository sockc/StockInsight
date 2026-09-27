#!/usr/bin/env bash
set -euo pipefail

KEYSTORE="${1:-stockinsight-release.jks}"
ALIAS="${2:-stockinsight}"

if [[ -e "$KEYSTORE" ]]; then
  echo "$KEYSTORE already exists. Refusing to overwrite the fixed release key." >&2
  exit 1
fi

command -v keytool >/dev/null || { echo "keytool not found; install JDK 17+." >&2; exit 1; }

keytool -genkeypair -v \
  -keystore "$KEYSTORE" \
  -alias "$ALIAS" \
  -keyalg RSA \
  -keysize 4096 \
  -validity 36500

if base64 --help 2>&1 | grep -q -- '-w'; then
  base64 -w0 "$KEYSTORE" > "$KEYSTORE.base64.txt"
else
  base64 "$KEYSTORE" | tr -d '\n' > "$KEYSTORE.base64.txt"
fi

echo "Created $KEYSTORE and $KEYSTORE.base64.txt"
echo "GitHub Secrets: SIGNING_KEY_BASE64, SIGNING_STORE_PASSWORD, SIGNING_KEY_ALIAS=$ALIAS, SIGNING_KEY_PASSWORD"
echo "Never commit the keystore or its Base64 export."

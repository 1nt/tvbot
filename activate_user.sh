#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"
COOKIES=$(cat "$COOKIE_FILE")

if [ $# -lt 1 ]; then
    echo "Usage: $0 <userId> [dateStop]"
    echo "Example: $0 850501"
    echo "Example with stop date: $0 850501 2026-07-20"
    exit 1
fi

USER_ID="$1"
DATE_STOP="${2:-}"

if [ -n "$DATE_STOP" ]; then
    curl -s -b "$COOKIES" -X POST \
        -d "userId=$USER_ID&dateStopAccount=$DATE_STOP" \
        "https://b.1lot.tv/dealer_iptv.php?action=activateUserAccount"
else
    curl -s -b "$COOKIES" -X POST \
        -d "userId=$USER_ID&dateStopAccount=" \
        "https://b.1lot.tv/dealer_iptv.php?action=activateUserAccount"
fi

echo ""
echo "Account activated for user $USER_ID"

#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"

if [ ! -f "$COOKIE_FILE" ]; then
    echo "Setup: save your browser cookies:"
    echo "  echo 'PHPSESSID=xxx; __ddg8_=yyy; __ddg9_=zzz; __ddg10_=www' > $COOKIE_FILE"
    exit 1
fi

COOKIES=$(cat "$COOKIE_FILE")

if [ $# -ne 4 ]; then
    echo "Usage: $0 <userId> <packet> <date YYYY-MM-DD> <dilerPay 0/1>"
    echo "Example: $0 850345 1024 2026-07-19 1"
    exit 1
fi

curl -s -b "$COOKIES" -X POST \
    -d "action=buyIptvPacket&packetId=$2&dateStopPacket=$3&dilerPay=$4&userId=$1" \
    "https://b.1lot.tv/dealer_iptv.php?action=buyIptvPacket"

echo ""

USER_PAGE=$(curl -s -b "$COOKIES" \
    "https://b.1lot.tv/dealer_iptv.php?action=adminUser&userId=$1")
PLAYLIST=$(echo "$USER_PAGE" | grep -oP 'https://[^"]+\.m3u8' | head -1)
echo "PLAYLIST=$PLAYLIST"
echo "Done for user $1"

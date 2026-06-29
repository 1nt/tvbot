#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"

if [ ! -f "$COOKIE_FILE" ]; then
    echo "Setup: echo 'PHPSESSID=xxx' > $COOKIE_FILE"
    exit 1
fi

COOKIES=$(cat "$COOKIE_FILE")

if [ $# -ne 6 ]; then
    echo "Usage: $0 <login> <password> <comment> <packet> <date> <dilerPay>"
    echo "Example: $0 testuser pass123 'no comments' 1024 2026-07-19 1"
    exit 1
fi

USERNAME="$1"
PASSWORD="$2"
COMMENT="$3"
PACKET="$4"
DATE="$5"
DILER_PAY="$6"

echo "Creating user $USERNAME..."
curl -s -b "$COOKIES" -X POST \
    -d "action=createNewUser&userNameNew=$USERNAME&userPassNew=$PASSWORD&userCommentNew=$COMMENT" \
    "https://b.1lot.tv/dealer_iptv.php?action=createNewUser" > /dev/null

sleep 1

echo "Getting userId..."
ADMIN_HTML=$(curl -s -b "$COOKIES" \
    "https://b.1lot.tv/dealer_iptv.php?action=adminUsers")

# Search by comment first, then by login
USER_ID=$(echo "$ADMIN_HTML" | grep ">$COMMENT<" -A1 | grep -oP "userId=\K\d+" | head -1)

if [ -z "$USER_ID" ]; then
    USER_ID=$(echo "$ADMIN_HTML" | grep "$USERNAME" | grep -oP "userId=\K\d+" | head -1)
fi

if [ -z "$USER_ID" ]; then
    echo "ERROR: Could not find userId for $USERNAME (comment: $COMMENT)"
    exit 1
fi

echo "USER_ID=$USER_ID"
echo "Buying subscription (packet=$PACKET, date=$DATE)..."

curl -s -b "$COOKIES" -X POST \
    -d "action=buyIptvPacket&packetId=$PACKET&dateStopPacket=$DATE&dilerPay=$DILER_PAY&userId=$USER_ID" \
    "https://b.1lot.tv/dealer_iptv.php?action=buyIptvPacket" > /dev/null

sleep 1

echo "Getting playlist link..."
USER_PAGE=$(curl -s -b "$COOKIES" \
    "https://b.1lot.tv/dealer_iptv.php?action=adminUser&userId=$USER_ID")
PLAYLIST=$(echo "$USER_PAGE" | grep -oP "https://[^\"]+\.m3u8" | head -1)

if [ -n "$PLAYLIST" ]; then
    echo "PLAYLIST=$PLAYLIST"
else
    echo "ERROR: Could not find playlist link"
fi

echo "DONE: User $USERNAME (ID=$USER_ID) created with subscription"

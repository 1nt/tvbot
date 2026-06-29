#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"

if [ ! -f "$COOKIE_FILE" ]; then
    echo "Setup: save your browser cookies:"
    echo "  echo 'PHPSESSID=xxx' > $COOKIE_FILE"
    exit 1
fi

COOKIES=$(cat "$COOKIE_FILE")

if [ $# -ne 3 ]; then
    echo "Usage: $0 <login> <password> <comment>"
    exit 1
fi

USERNAME="$1"
PASSWORD="$2"
COMMENT="$3"

curl -s -b "$COOKIES" -X POST \
    -d "action=createNewUser&userNameNew=$USERNAME&userPassNew=$PASSWORD&userCommentNew=$COMMENT" \
    "https://b.1lot.tv/dealer_iptv.php?action=createNewUser" > /dev/null

sleep 1

ADMIN_HTML=$(curl -s -b "$COOKIES" \
    "https://b.1lot.tv/dealer_iptv.php?action=adminUsers")

# Try to find by comment first (tg_id is stored in comment)
USER_ID=$(echo "$ADMIN_HTML" | grep ">$COMMENT<" -A1 | grep -oP "userId=\K\d+" | head -1)

# If not found by comment, try by login
if [ -z "$USER_ID" ]; then
    USER_ID=$(echo "$ADMIN_HTML" | grep "$USERNAME" | grep -oP "userId=\K\d+" | head -1)
fi

if [ -n "$USER_ID" ]; then
    echo "USER_ID=$USER_ID"
    USER_PAGE=$(curl -s -b "$COOKIES" \
        "https://b.1lot.tv/dealer_iptv.php?action=adminUser&userId=$USER_ID")
    PLAYLIST=$(echo "$USER_PAGE" | grep -oP "https://[^\"]+\.m3u8" | head -1)
    echo "PLAYLIST=$PLAYLIST"
else
    echo "ERROR: Could not find userId for $USERNAME (comment: $COMMENT)"
fi

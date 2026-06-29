#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"
COOKIES=$(cat "$COOKIE_FILE")

if [ $# -ne 2 ]; then
    echo "Usage: $0 <username> <amount>"
    echo "Example: $0 testuser 0.02"
    exit 1
fi

USERNAME="$1"
AMOUNT="$2"

curl -s -b "$COOKIES" -X POST \
    -d "userTrans=$USERNAME&moneyTrans=$AMOUNT" \
    "https://b.1lot.tv/dealer_iptv.php?action=transMoneyToYourUser"

echo ""
echo "Transferred $AMOUNT to $USERNAME"

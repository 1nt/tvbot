#!/bin/bash

COOKIE_FILE="/root/tvbot/.cookie_string"

if [ ! -f "$COOKIE_FILE" ]; then
    exit 0
fi

COOKIES=$(cat "$COOKIE_FILE")
curl -s -b "$COOKIES" "https://b.1lot.tv/dealer_iptv.php?action=adminUsers" > /dev/null

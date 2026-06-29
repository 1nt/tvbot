#!/bin/bash
COOKIE_FILE="/root/tvbot/.cookie_string"
COOKIES=$(cat "$COOKIE_FILE")
curl -s --connect-timeout 10 --max-time 20 -b "$COOKIES" "$1"

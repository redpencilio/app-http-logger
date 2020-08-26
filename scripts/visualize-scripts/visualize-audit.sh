#!/bin/sh

echo -n "Enter key passphrase: "
read -r -s passphrase
echo

passphrasefile=$(mktemp)
echo "$passphrase" > "$passphrasefile"

gpg --import /project/gpg.key

python3 ./visualize-audit.py "$1" "$passphrasefile" 'http://elasticsearch:9200' audit /project/encrypted/*
rm "$passphrasefile"

#!/bin/sh

echo -n "Enter key passphrase: "
read -r -s passphrase
echo

passphrasefile=$(mktemp)
echo "$passphrase" > "$passphrasefile"

echo "$passphrase" | gpg --import --pinentry-mode loopback /project/keys/gpg.key

python3 ./visualize-audit.py "$1" "$passphrasefile" 'http://elasticsearch:9200' http-log /project/data/encrypted/http/*
rm "$passphrasefile"

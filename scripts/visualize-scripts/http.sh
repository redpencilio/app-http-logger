#!/bin/sh

echo -n "Enter key passphrase: "
read -r -s passphrase
echo

echo "$passphrase" | gpg --batch --import --pinentry-mode loopback /project/keys/gpg.key

es_index="http-log"
echo "Going to import logs in Elasticsearch index $es_index"

python3 ./import-logs.py "$1" "$passphrase" 'http://elasticsearch:9200' "$es_index" $2 /project/data/encrypted/http/*

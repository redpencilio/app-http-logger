#!/bin/sh
echo
echo -n "Enter key passphrase: "
read -r -s passphrase
echo

echo "$passphrase" | gpg --batch --import --pinentry-mode loopback /project/keys/gpg.key

recipient=$1
es_index="http-log"
batch_size=${2:-1000} # fallback to default: 1000
echo "Going to import HTTP logs in Elasticsearch index $es_index (batch size $batch_size)"

python3 ./import-logs.py "$recipient" "$passphrase" 'http://elasticsearch:9200' "$es_index" $batch_size /project/data/encrypted/http/*

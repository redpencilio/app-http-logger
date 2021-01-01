#!/bin/sh

echo -n "Enter key passphrase: "
read -r -s passphrase
echo

passphrasefile=$(mktemp)
echo "$passphrase" > "$passphrasefile"

echo "$passphrase" | gpg --batch --import --pinentry-mode loopback /project/keys/gpg.key

date=`date +%Y%m%d%H%M%S`
es_index="http-log-$date"
echo "Going to import logs in Elasticsearch index $es_index"

python3 ./import-logs.py "$1" "$passphrasefile" 'http://elasticsearch:9200' "$es_index" /project/data/encrypted/http/*
rm "$passphrasefile"

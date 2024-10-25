#!/bin/sh

export GNUPGHOME="/root/.gnupg/"
mkdir -p /root/.gnupg/
chmod go-rwx /root/.gnupg/
echo "auto-expand-secmem 0x30000" > /root/.gnupg/gpg-agent.conf

RECIPIENT=$1

echo ""
echo -n "Enter key passphrase: "
read -r -s PASSPHRASE
echo ""

# Add the key and unlock it
echo "$PASSPHRASE" | gpg --batch --import --pinentry-mode loopback /project/keys/gpg.key

ES_INDEX="http-log"
BATCH_SIZE=${3:-1000} # fallback to default: 1000
THREADS=${2:-1}
echo "Going to import HTTP logs in Elasticsearch index $ES_INDEX (batch size $BATCH_SIZE) (parallel $THREADS)"

python3 ./import-logs.py "$RECIPIENT" "$PASSPHRASE" 'http://elasticsearch:9200' "$ES_INDEX" $BATCH_SIZE $THREADS /project/data/encrypted/http/*

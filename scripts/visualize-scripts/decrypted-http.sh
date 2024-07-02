#!/bin/sh
ES_INDEX="http-log"
BATCH_SIZE=${4:-1000} # fallback to default: 1000
THREADS=${3:-1}
echo
echo "Going to import HTTP logs in Elasticsearch index $ES_INDEX (batch size $BATCH_SIZE) (parallel $THREADS)"
python3 ./import-logs.py "" "" 'http://elasticsearch:9200' "$ES_INDEX" $BATCH_SIZE $THREADS  /project/data/decrypted/http/*

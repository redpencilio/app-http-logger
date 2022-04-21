#!/bin/sh
ES_INDEX="stats"
THREADS=${1:-1}
BATCH_SIZE=${2:-1000} # fallback to default: 1000
echo
echo "Going to import stats logs in Elasticsearch index $ES_INDEX (batch size $BATCH_SIZE)"
python3 ./import-logs.py "" "" 'http://elasticsearch:9200' "$ES_INDEX" $BATCH_SIZE $THREADS  /project/data/compressed/stats/*

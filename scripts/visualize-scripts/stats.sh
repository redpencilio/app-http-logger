#!/bin/sh
es_index="stats"
batch_size=${1:-1000} # fallback to default: 1000
echo
echo "Going to import stats logs in Elasticsearch index $es_index (batch size $batch_size)"
python3 ./import-logs.py "" "" 'http://elasticsearch:9200' "$es_index" $batch_size /project/data/compressed/stats/*

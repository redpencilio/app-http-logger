#!/bin/sh
es_index="stats"
echo "Going to import logs in Elasticsearch index $es_index"
python3 ./import-logs.py "" "" 'http://elasticsearch:9200' "$es_index" /project/data/compressed/stats/*

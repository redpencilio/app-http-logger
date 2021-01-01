#!/bin/sh

date=`date +%Y%m%d%H%M%S`
es_index="stats-$date"
echo "Going to import logs in Elasticsearch index $es_index"
python3 ./import-logs.py "" "" 'http://elasticsearch:9200' "$es_index" /project/data/logs/stats/*

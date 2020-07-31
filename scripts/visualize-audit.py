#!/bin/env python3

import json
import requests
import sys
import os.path

# Read input

if len(sys.argv) < 4:
    print("Usage: ./visualize-audit.py URL INDEX FILE...")
    exit(1)

url = sys.argv[1]

index = sys.argv[2]

for arg in sys.argv[3:]:
    if not os.path.isfile(arg):
        print("{0:s} is not a file.".format(arg))
        print("Usage: ./visualize-audit.py URL INDEX FILE...")
        exit(1)

events = []

for file in sys.argv[3:]:
    with open(file) as f:
        events += [line.rstrip('\n') for line in f]

# Prepare input for request

command = '{{ "index" : {{ "_index" : "{0:s}" }} }}'.format(index)

def to_bulk_query(events):
    for event in events:
        yield command
        yield event

# Send request to Bulk API
bulkdata = '\n'.join([line for line in to_bulk_query(events)]) + '\n'
headers = { 'content-type' : 'application/json' }
r = requests.post("{0:s}/_bulk".format(url), data=bulkdata, headers=headers)

print(bulkdata)

print("Response: {0:d}".format(r.status_code))
print(json.loads(r.text))

#!/bin/env python3

import json
import requests
import sys
import os.path
import subprocess

# Get JSON events from file
def get_events(filename, recipient, passphrase_file):
    with open(filename) as f:
        # Just read the file
        if filename.endswith(".json"):
            return [line.rstrip('\n') for line in f]

        # Decrypt and then read the output
        elif filename.endswith(".json.gpg"):
            subproc = subprocess.run(["/usr/bin/gpg", "--decrypt", "--recipient", recipient, "--passphrase-file", passphrase_file, "--trust-model", "always", "--batch", "--pinentry-mode", "loopback"],
                                     stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(subproc.stderr.decode("utf-8"))
            subproc.check_returncode()
            return [line.rstrip('\n') for line in subproc.stdout.decode("utf-8").splitlines()]

# Check input
if len(sys.argv) < 6:
    print("Usage: ./import-logs.py RECIPIENT PASSPHRASE_FILE URL INDEX FILE...")
    exit(1)

for arg in sys.argv[5:]:
    if not os.path.isfile(arg):
        print("{0:s} is not a file.".format(arg))
        print("Usage: ./import-logs.py RECIPIENT PASSPHRASE_FILE URL INDEX FILE...")
        exit(1)

# Assign variables
url = sys.argv[3]

index = sys.argv[4]

command = '{{ "index" : {{ "_index" : "{0:s}" }} }}'.format(index)
def to_bulk_query(events):
    for event in events:
        yield command
        yield event

# Send input to Bulk API file-per-file
for filename in sys.argv[5:]:
    # Get events in file
    events = get_events(filename, sys.argv[1], sys.argv[2])

    if events:
        # Format events for Elasticsearch
        bulkdata = '\n'.join([line for line in to_bulk_query(events)]) + '\n'
        bulkdata = bulkdata.encode(encoding='utf-8')

        # Send request to Bulk API
        headers = { 'content-type' : 'application/json' }
        r = requests.post("{0:s}/_bulk".format(url), data=bulkdata, headers=headers)

        # Print result
        print("Ingested file: {0:s}".format(filename))
        print("Response: {0:d}".format(r.status_code))
    else:
        print("Skipped file: {0:s}".format(filename))

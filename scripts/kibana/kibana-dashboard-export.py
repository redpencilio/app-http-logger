#!/bin/env python3

import json
import requests
import sys
import os.path
import pathlib

if len(sys.argv) < 3:
    print("Usage: ./kibana-dashboard-export.py KIBANA-HOST DASHBOARD-DIR")

# Create the dashboards folder if it doesnt exist already
pathlib.Path(sys.argv[2]).mkdir(exist_ok=True)

headers = {'kbn-xsrf': 'true', 'Content-Type': 'application/json'}

# Get all dashboard objects
r = requests.get("http://{0:s}/api/saved_objects/_find?type=dashboard&per_page=200".format(sys.argv[1]), headers=headers)

# Save the dashboard objects
for item in r.json()['saved_objects']:
    exportResp = requests.post(
        "http://{0:s}/api/saved_objects/_export".format(sys.argv[1]),
        json={"objects": [{"type": "dashboard", "id": item['id']}], "includeReferencesDeep": True},
        headers=headers
    )
    with open("{0:s}/{1:s}.ndjson".format(sys.argv[2], item['id']), "w") as f:
        print("Writing dashboard '{0:s}' to {1:s}.ndjson".format(item['attributes']['title'], item['id']))
        f.write(exportResp.text)

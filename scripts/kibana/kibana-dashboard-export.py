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

# Get all dashboard objects
r = requests.get("http://{0:s}/api/saved_objects/_find?type=dashboard&per_page=200".format(sys.argv[1]))

# Save the dashboard objects
for item in r.json()['saved_objects']:
    dashboardResp = requests.get("http://{0:s}/api/kibana/dashboards/export?dashboard={1:s}".format(sys.argv[1], item['id']))
    with open("{0:s}/{1:s}.json".format(sys.argv[2], item['id']), "w") as f: # Open file in "w" = truncate and write mode
        print("Writing dashboard {0:s} to {1:s}.json".format(item['attributes']['title'], item['id']))
        f.write(dashboardResp.text)

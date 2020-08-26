#!/bin/env python3

import json
import requests
import sys
import os.path
import pathlib

# Create the dashboards folder if it doesnt exist already
pathlib.Path("./dashboards").mkdir(exist_ok=True)

# Get all dashboard objects
r = requests.get("http://localhost:5601/api/saved_objects/_find?type=dashboard&per_page=200")

# Save the dashboard objects
for item in r.json()['saved_objects']:
    dashboardResp = requests.get("http://localhost:5601/api/kibana/dashboards/export?dashboard={0:s}".format(item['id']))
    with open("./dashboards/{0:s}.json".format(item['id']), "w") as f: # Open file in "w" = truncate and write mode
        print("Writing dashboard {0:s} to {1:s}.json".format(item['attributes']['title'], item['id']))
        f.write(dashboardResp.text)

#!/bin/env python3

import json
import requests
import sys
import pathlib
import os

if len(sys.argv) < 3:
    print("Usage: ./kibana-dashboard-import.py KIBANA-HOST DASHBOARD-DIR")

dashboardDir = pathlib.Path(sys.argv[2])

if not dashboardDir.is_dir():
    print("No 'dashboards' directory found under current folder")
    sys.exit(1)

print("Importing all dashboards found in 'dashboards' directory")
for filePath in dashboardDir.iterdir():
    if not filePath.is_file():
        continue

    r = requests.post("http://{0:s}/api/kibana/dashboards/import".format(sys.argv[1]), data=filePath.read_text(), headers={'kbn-xsrf' : 'true'})
    print("- [Response status {0}] {1}".format(r.status_code, os.path.basename(filePath)));

#!/bin/env python3

import json
import requests
import sys
import pathlib

dashboardDir = pathlib.Path('./dashboards')

if not dashboardDir.is_dir():
    print("No 'dashboards' directory found under current folder")
    sys.exit(1)

for filePath in dashboardDir.iterdir():
    if not filePath.is_file():
        continue

    r = requests.post("http://localhost:5601/api/kibana/dashboards/import", data=filePath.read_text(), headers={'kbn-xsrf' : 'true'})
    print(r.text);

#!/bin/sh

pip install requests

python3 ./kibana-dashboard-export.py 'kibana:5601' /project/dashboards

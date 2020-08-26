#!/bin/sh

pip install requests

python3 ./kibana-dashboard-import.py 'kibana:5601' /project/dashboards

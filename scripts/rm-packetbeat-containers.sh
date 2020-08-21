#!/bin/sh

docker ps | grep "\-monitor" | awk '{ print $1 }' | xargs docker rm -f

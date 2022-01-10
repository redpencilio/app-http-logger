#!/bin/sh

docker ps -a | grep "\-monitor" | awk '{ print $1 }' | xargs docker rm -f

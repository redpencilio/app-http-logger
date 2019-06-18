#! /bin/env bash

docker ps | grep crccheck | awk '{ print $1 }' | xargs docker rm -f

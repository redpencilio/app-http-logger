#!/bin/sh

docker ps | grep "-packetbeat" | awk '{ print $1 }' | xargs docker rm -f

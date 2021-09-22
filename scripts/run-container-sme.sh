#!/usr/bin/env bash

docker stop StatisticalMe
docker rm StatisticalMe

# --memory 500m
docker run --detach --restart always --name StatisticalMe --volume "$(readlink -f ~/var-sme):/opt/statisticalme/var" localhost/statisticalme:latest

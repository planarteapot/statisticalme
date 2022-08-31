#!/usr/bin/env bash

docker stop StatisticalMe
docker rm StatisticalMe

# --memory 500m
docker run --detach --name StatisticalMe --volume "$(readlink -f ~/var-testing):/homesme/var" statisticalme:latest

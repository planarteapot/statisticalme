#!/usr/bin/env bash

docker stop StatisticalMe
docker rm StatisticalMe

docker run --detach --name StatisticalMe --volume "$(readlink -f ~/var-testing):/opt/statisticalme/var" statisticalme:latest

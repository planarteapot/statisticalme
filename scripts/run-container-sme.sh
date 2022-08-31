#!/usr/bin/env bash

docker stop StatisticalMe
docker rm StatisticalMe

docker run --detach --restart always --name StatisticalMe --volume "$(readlink -f ~/var-sme):/homesme/var" localhost/statisticalme:latest

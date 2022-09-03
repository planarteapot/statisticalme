#!/usr/bin/env bash

docker stop StatisticalMe
docker rm StatisticalMe

docker run --detach --restart always --name StatisticalMe --user $(id -u):$(id -g) --volume "$(readlink -f ~/var-sme):/opt/statisticalme/var" statisticalme:latest

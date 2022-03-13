#!/usr/bin/env bash

podman stop StatisticalMe
podman rm StatisticalMe

# --memory 500m
podman run --detach --restart always --name StatisticalMe --volume "$(readlink -f ~/var-sme):/opt/statisticalme/var" localhost/statisticalme:latest

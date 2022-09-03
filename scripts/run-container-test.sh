#!/usr/bin/env bash

docker stop SmeTestBot
docker rm SmeTestBot

docker run --detach --name SmeTestBot --user $(id -u):$(id -g) --volume "$(readlink -f ~/var-testing):/opt/statisticalme/var" statisticalme:latest

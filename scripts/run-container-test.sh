#!/usr/bin/env bash

docker stop SmeTestBot
docker rm SmeTestBot

docker run --detach --name SmeTestBot --volume "$(readlink -f ~/var-testing):/opt/statisticalme/var" statisticalme:latest

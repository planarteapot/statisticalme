#!/usr/bin/env bash

set -o errexit

cont=$(buildah from sme-reqs:latest)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" $cont

buildah run $cont mkdir -p /opt/statisticalme /opt/statisticalme/data /opt/statisticalme/var

buildah run $cont pip3 install .
buildah copy $cont data/values-*.txt /opt/statisticalme/data

buildah config --workingdir /opt/statisticalme $cont
buildah config --entrypoint '["python3", "main.py"]' $cont

buildah commit --format docker $cont statisticalme:latest

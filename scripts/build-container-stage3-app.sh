#!/usr/bin/env bash

set -o errexit

# Wheel prebuild

/bin/rm -rf dist/*
${HOME}/.venv/sme_deploy/bin/python3 setup.py bdist_wheel
wheelname=$(ls dist/statisticalme-*-py3-none-any.whl)
echo "Destination wheel name $wheelname"

# Containerize

cont=$(buildah from sme-reqs:latest)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" $cont

buildah run $cont mkdir -p /opt/statisticalme /opt/statisticalme/data /opt/statisticalme/var

buildah run --volume $(readlink -f .):/src_sme $cont pip3 install --no-use-pep517 /src_sme/${wheelname}
buildah copy $cont data/values-*.txt /opt/statisticalme/data

buildah config --workingdir /opt/statisticalme $cont
buildah config --entrypoint '["python3", "-m", "statisticalme"]' $cont

buildah commit --format docker $cont statisticalme:latest

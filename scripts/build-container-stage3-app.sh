#!/usr/bin/env bash

set -o errexit

# Wheel prebuild

/bin/rm -rf target/wheels/
${HOME}/.venv/sme_deploy/bin/maturin build --bindings pyo3 --manylinux 2010 --release
wheelname=$(ls target/wheels/statisticalme-*-cp38-cp38-manylinux2010_x86_64.whl)
echo "Destination wheel name $wheelname"

# Containerize

cont=$(buildah from sme-reqs:latest)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" $cont

buildah run $cont mkdir -p /opt/statisticalme /opt/statisticalme/data /opt/statisticalme/var

buildah run --volume $(readlink -f .):/src_sme $cont pip3 install /src_sme/${wheelname}
buildah copy $cont data/values-*.txt /opt/statisticalme/data

buildah config --workingdir /opt/statisticalme $cont
buildah config --entrypoint '["python3", "-m", "statisticalme"]' $cont

buildah commit --format docker $cont statisticalme:latest

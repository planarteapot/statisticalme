#!/usr/bin/env bash

set -o errexit

# Wheel prebuild

/bin/rm -rf target/wheels/
"${HOME}"/.venv/sme_deploy/bin/maturin build --bindings pyo3 --compatibility linux --release
wheelname=$(ls target/wheels/statisticalme-*-cp39-cp39-linux_x86_64.whl)
echo "Destination wheel name $wheelname"

# Containerize

cont=$(buildah from sme-reqs:latest)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" "$cont"

buildah run "$cont" mkdir -p /opt/statisticalme /opt/statisticalme/var

buildah run --volume "$(readlink -f .):/src_sme" "$cont" pip install /src_sme/"${wheelname}"

buildah config --workingdir /opt/statisticalme "$cont"
buildah config --entrypoint '["python3", "-m", "statisticalme"]' "$cont"

buildah unmount "$cont"
buildah commit --format docker "$cont" statisticalme:latest
buildah rm "$cont"

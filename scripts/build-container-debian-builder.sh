#!/usr/bin/env bash

set -o errexit

cont=$(buildah from rust:slim-bullseye)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" "$cont"
buildah config --env 'DEBIAN_FRONTEND=noninteractive' "$cont"

buildah run "$cont" apt-get update
buildah run "$cont" apt-get -y full-upgrade --no-install-recommends
buildah run "$cont" apt-get -y install --no-install-recommends python-is-python3 python3-minimal python3-venv python3-distutils python3-pip
buildah run "$cont" apt-get -y install --no-install-recommends libxml2 libxslt1.1 zlib1g
buildah run "$cont" apt-get -y install --no-install-recommends python-dev-is-python3 python3-dev python-pip-whl binutils binfmt-support make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev patch

buildah run "$cont" python3 -m venv /root/venv-build
buildah config --env 'PATH=/root/venv-build/bin:$PATH' "$cont"
buildah config --env 'VIRTUAL_ENV=/root/venv-build' "$cont"

buildah run "$cont" python -m ensurepip
buildah run "$cont" pip install wheel
buildah run "$cont" pip install -U pip
buildah run "$cont" pip install maturin

buildah run "$cont" rm -rf "/root/.cache"

buildah run "$cont" apt-get -y autoremove
buildah run "$cont" apt-get clean
buildah run "$cont" find /var/lib/apt/lists -type f -not -empty -delete

buildah unmount "$cont"
buildah commit --format docker "$cont" sme-debian-builder:latest
buildah rm "$cont"

# to use:
# > podman run --rm --tty --volume $(pwd):/work --workdir /work sme-debian-builder cargo build --target-dir target-bullseye

#!/usr/bin/env bash

set -o errexit

# cont=$(buildah from ubuntu:21.10)
cont=$(buildah from debian:bullseye-slim)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" "$cont"
buildah config --env 'DEBIAN_FRONTEND=noninteractive' "$cont"

buildah run "$cont" apt-get update
buildah run "$cont" apt-get -y full-upgrade --no-install-recommends
buildah run "$cont" apt-get -y install --no-install-recommends python-is-python3 python3-minimal python3-venv python3-distutils

buildah run "$cont" apt-get -y autoremove
buildah run "$cont" apt-get clean
buildah run "$cont" find /var/lib/apt/lists -type f -not -empty -delete

buildah unmount "$cont"
buildah commit --format docker "$cont" sme-python3-base:latest
buildah rm "$cont"

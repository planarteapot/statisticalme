#!/usr/bin/env bash

set -o errexit

cont=$(buildah from debian:testing-slim)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" $cont

buildah run $cont apt-get update
buildah run $cont apt-get -y full-upgrade --no-install-recommends
buildah run $cont apt-get -y install --no-install-recommends pypy3

buildah run $cont apt-get -y autoremove
buildah run $cont apt-get clean
buildah run $cont find /var/lib/apt/lists -type f -not -empty -delete

buildah commit --format docker $cont sme-base:latest

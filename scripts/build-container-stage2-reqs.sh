#!/usr/bin/env bash

set -o errexit

cont=$(buildah from sme-base:latest)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" $cont

buildah run $cont mkdir -p /opt/statisticalme /opt/statisticalme/data /opt/statisticalme/var

buildah copy $cont requirements.txt /opt/statisticalme

buildah config --env 'DEBIAN_FRONTEND=noninteractive' $cont

buildah run $cont apt-get update
buildah run $cont apt-get -y install --no-install-recommends libxml2 libxslt1.1 zlib1g
buildah run $cont apt-get -y install --no-install-recommends pypy3-dev python-pip-whl make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev

buildah run $cont pypy3 -m venv /root/venv-sme
buildah config --env 'PATH=/root/venv-sme/bin:$PATH' $cont
buildah config --env 'VIRTUAL_ENV=/root/venv-sme' $cont

buildah run $cont pip3 install --no-use-pep517 wheel
buildah run $cont pip3 install --no-use-pep517 --requirement /opt/statisticalme/requirements.txt

buildah run $cont apt-get -y purge pypy3-dev python-pip-whl make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev

buildah run $cont apt-get -y autoremove
buildah run $cont apt-get clean
buildah run $cont find /var/lib/apt/lists -type f -not -empty -delete

buildah run $cont rm -f /opt/statisticalme/requirements.txt

buildah commit --format docker $cont sme-reqs:latest

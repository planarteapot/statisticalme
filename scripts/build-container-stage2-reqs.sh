#!/usr/bin/env bash

set -o errexit

cont=$(buildah from python3-base:latest)

buildah config --label maintainer="Antony <dentad@users.noreply.github.com>" $cont
buildah config --env 'DEBIAN_FRONTEND=noninteractive' $cont

buildah run $cont mkdir -p /opt
buildah copy $cont requirements.txt /opt

buildah run $cont apt-get update
buildah run $cont apt-get -y install --no-install-recommends libxml2 libxslt1.1 zlib1g
buildah run $cont apt-get -y install --no-install-recommends python-dev-is-python3 python3-dev python-pip-whl binutils binfmt-support make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev patch

buildah run $cont python3 -m venv /root/venv-sme
buildah config --env 'PATH=/root/venv-sme/bin:$PATH' $cont
buildah config --env 'VIRTUAL_ENV=/root/venv-sme' $cont

buildah run $cont python3 -m ensurepip
buildah run $cont pip install -U pip
buildah run $cont pip install wheel
buildah run $cont pip install --requirement /opt/requirements.txt

buildah run $cont rm -rf "/root/.cache"
buildah run $cont apt-get -y purge python-dev-is-python3 python3-dev python-pip-whl binutils binfmt-support make gcc g++ libxml2-dev libxslt1-dev zlib1g-dev patch

# buildah run $cont apt-get -y purge binutils binutils-common binutils-x86-64-linux-gnu libbinutils libctf0 libctf-nobfd0 libjs-jquery
buildah run $cont apt-get -y purge libjs-jquery
buildah run $cont apt-get -y autoremove
buildah run $cont apt-get clean
buildah run $cont dpkg -P apt ubuntu-keyring gpgv
buildah run $cont rm -rf /var/lib/apt

buildah run $cont rm -f /opt/requirements.txt

buildah unmount $cont
buildah commit --format docker $cont sme-reqs:latest
buildah rm $cont

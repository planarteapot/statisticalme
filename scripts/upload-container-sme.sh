#!/bin/bash

# Run locally.

mkdir -p sme-ocidir
rm -rf sme-ocidir/*

# podman save --compress --format oci-dir --output sme-ocidir statisticalme:latest
podman save --compress --format docker-archive statisticalme:latest > smecon.tar

rsync -av smecon.tar sme@watcherstower:

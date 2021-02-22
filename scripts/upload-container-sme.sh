#!/bin/bash

# Run locally.

SMECONTAR_NAME=$(tempfile -s .tar)

# mkdir -p sme-ocidir
# rm -rf sme-ocidir/*

# podman save --compress --format oci-dir --output sme-ocidir statisticalme:latest
podman save --compress --format docker-archive statisticalme:latest > "$SMECONTAR_NAME"
rsync -av --info=progress2 "$SMECONTAR_NAME" bontstowersme:smecon.tar
rm "$SMECONTAR_NAME"

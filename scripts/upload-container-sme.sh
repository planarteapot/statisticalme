#!/bin/bash

# Run locally.

SMECONTAR_NAME=$(mktemp --suffix .tar)

docker save statisticalme:latest > "$SMECONTAR_NAME"
rsync -av --info=progress2 "$SMECONTAR_NAME" bontstowersme:smecon.tar

rm "$SMECONTAR_NAME"

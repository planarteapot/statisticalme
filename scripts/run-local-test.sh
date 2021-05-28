#!/usr/bin/env bash

# Assume a venv sme_debug or similar is active

set -o errexit

# Wheel prebuild

/bin/rm -rf target/wheels/
${HOME}/.venv/sme_deploy/bin/maturin develop --binding-crate pyo3
# wheelname=$(ls target/wheels/statisticalme-*-cp38-cp38-manylinux2010_x86_64.whl)
# echo "Destination wheel name $wheelname"

# #

# pip install --force "${wheelname}"

export RUST_BACKTRACE=1
python3 -m statisticalme

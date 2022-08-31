#!/usr/bin/env bash

# Assume a venv sme_local or similar is active

set -o errexit

/bin/rm -rf target/wheels/
"${HOME}"/.venv/sme_deploy/bin/maturin develop --bindings pyo3

# wheelname=$(ls target/wheels/statisticalme-*-cp310-cp310-linux_x86_64.whl)
# echo "Destination wheel name $wheelname"

# pip install --force "${wheelname}"

export RUST_BACKTRACE=1
python3 -m statisticalme

#!/bin/bash

scp -p sme@timtower:var-sme/env.sh ./env.sh.copy
scp -p sme@timtower:var-sme/persdata.yaml ./
scp -p sme@timtower:var-sme/config.yaml ./

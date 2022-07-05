#!/bin/bash

scp -p bontstowersme:var-sme/env.sh ./env.sh.copy
scp -p bontstowersme:var-sme/persdata.json ./
scp -p bontstowersme:var-sme/config.json ./
scp -p bontstowersme:var-sme/weights.json ./

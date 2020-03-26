#!/bin/bash

# for Clear Linux

sudo swupd update
sudo hostnamectl set-hostname timtower

# reboot

sudo swupd bundle-add sysadmin-basic
sudo swupd bundle-add network-basic
sudo swupd bundle-add containers-basic
sudo swupd bundle-add vim

sudo useradd -m -c "StatisticalMe" sme
sudo usermod -aG docker sme
sudo passwd -l sme

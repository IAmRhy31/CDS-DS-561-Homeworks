#!/bin/bash
sudo apt update
sudo apt install python3
sudo apt install -y python3-pip

gsutil cp gs://app1-access/app1/requirements.txt /tmp/
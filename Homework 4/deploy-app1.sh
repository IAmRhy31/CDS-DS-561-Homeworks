#!/bin/bash
sudo apt-get update
sudo apt-get install python3 python3-pip

gsutil cp gs://app1-access/app1/requirements.txt /tmp/requirements.txt
pip3 install -r /tmp/requirements.txt

gsutil cp gs://app1-access/app1/main.py /tmp/main.py

cd /tmp

python3 main.py
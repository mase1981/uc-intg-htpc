#!/bin/bash

cd /app
pip install --no-cache-dir -q -r requirements.txt
python uc_intg_htpc/driver.py
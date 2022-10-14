#!/bin/bash
set -e -x

cd /icebox/core
pip install -r requirements.txt
pip install -r requirements-priv.txt
python setup.py develop
$@

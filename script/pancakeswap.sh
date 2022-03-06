#!/bin/bash

#echo START
cd || { echo "cd failed"; exit 1; }
cd pancakeswap-bot || { echo "cd pancakeswap-bot failed"; exit 1; }
source venv/bin/activate
python3 main.py
deactivate
#echo FINNISH

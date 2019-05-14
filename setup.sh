#!/usr/bin/env bash
pip install karel
wd=`pwd`
echo -e '\nexport PYTHONPATH=$PYTHONPATH:'$wd>>~/.bashrc

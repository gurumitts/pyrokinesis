#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

if [ -z "$1" ]; then
    echo "Target temp is required"
    exit 1
fi


echo starting control with target temp: $1
nohup sudo python control.py $1 >control.log 2>&1 &

echo starting web frontend
nohup sudo python web.py >web.log 2>&1 &

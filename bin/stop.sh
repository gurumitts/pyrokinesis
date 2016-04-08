#!/bin/bash


echo stopping
kill -9 `ps aux | grep run.py | awk '{print $2}'`


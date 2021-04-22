#!/usr/bin/env bash

git pull origin
nohup python server.py &
disown
echo "Done"

#!/usr/bin/env bash

git pull origin
chmod +x ./server.py
nohup ./server.py &

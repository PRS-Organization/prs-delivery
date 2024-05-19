#!/bin/bash

# Find processes with port 8000 and kill them
netstat -ap | grep 8000 | awk '{print $7}' | awk -F '/' '{print $1}' | while read -r pid; do
    echo "Killing process with PID: $pid"
    kill -9 "$pid"
done

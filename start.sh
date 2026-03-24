#!/usr/bin/env bash

echo "Starting news engine..."
python main.py &

echo "Starting API..."
python api.py
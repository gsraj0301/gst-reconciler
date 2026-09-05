#!/bin/bash
cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed."
    exit 1
fi

if ! python3 -c "import pandas, openpyxl, tkinterdnd2" &> /dev/null; then
    echo "Installing dependencies, please wait..."
    pip3 install -r requirements.txt --break-system-packages || pip3 install -r requirements.txt
fi

echo "Starting GST Reconciler..."
python3 run.py

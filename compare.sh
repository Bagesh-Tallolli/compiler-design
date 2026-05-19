#!/bin/bash
# Semantic Diff Analyzer - Compare Script

if [ "$#" -lt 2 ]; then
    echo "Usage: ./compare.sh <old.cpp> <new.cpp>"
    exit 1
fi

OLD_FILE=$1
NEW_FILE=$2

# Create required folders
mkdir -p .temp_ir

echo "Running Semantic Diff Analyzer..."
python -m src.cli compare "$OLD_FILE" "$NEW_FILE" -o semantic_report.txt

if [ $? -eq 0 ]; then
    echo "Report successfully generated at semantic_report.txt"
else
    echo "Error occurred during analysis."
    exit 1
fi

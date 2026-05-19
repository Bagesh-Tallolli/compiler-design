#!/bin/bash
# Semantic Diff Analyzer - Build Script

echo "Building Semantic Diff Analyzer..."

# 1. Create required folders
mkdir -p .temp_ir
mkdir -p uploads
mkdir -p testcases
mkdir -p evaluation

echo "1. Installing backend dependencies..."
pip install -r src/requirements.txt
if [ $? -ne 0 ]; then
    echo "Warning: Python pip not found or failed to install requirements."
fi

echo "2. Installing frontend dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "Warning: npm install failed. Please ensure Node.js is installed."
fi
cd ..

echo "3. Verifying LLVM installation..."
python -c "
import sys, shutil, subprocess
clang = shutil.which('clang++') or shutil.which('clang')
if not clang:
    print('Warning: clang not found in PATH')
    sys.exit(1)
try:
    ver = subprocess.run([clang, '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    print(f'Detected: {ver}')
except Exception:
    print('Warning: failed to get clang version')
"
if [ $? -ne 0 ]; then
    echo "LLVM verification failed. Please install LLVM 17+ and ensure clang is in PATH."
fi

echo "Build complete. You can now use ./run.sh or ./compare.sh"

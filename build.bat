@echo off
echo Building Semantic Diff Analyzer...

:: 1. Create required folders
if not exist .temp_ir mkdir .temp_ir
if not exist uploads mkdir uploads
if not exist testcases mkdir testcases
if not exist evaluation mkdir evaluation

echo 1. Installing backend dependencies...
pip install -r src/requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Warning: Python pip not found or failed to install requirements.
)

echo 2. Installing frontend dependencies...
cd frontend
call npm install
if %ERRORLEVEL% neq 0 (
    echo Warning: npm install failed. Please ensure Node.js is installed.
)
cd ..

echo 3. Verifying LLVM installation...
python -c "import sys, shutil; clang = shutil.which('clang++') or shutil.which('clang'); print('Clang found:', clang) if clang else print('Clang not found in PATH'); sys.exit(0 if clang else 1)"
if %ERRORLEVEL% neq 0 (
    echo LLVM verification failed. Please install LLVM 17+ and ensure clang is in PATH.
)

echo Build complete. You can now use run.bat or compare.bat

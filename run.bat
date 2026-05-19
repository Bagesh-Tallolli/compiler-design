@echo off
echo Starting Semantic Diff Analyzer...

if not exist .temp_ir mkdir .temp_ir
if not exist uploads mkdir uploads

echo Starting backend...
start /B python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

echo Waiting for backend to be ready...
:loop
curl -s http://localhost:8000/api/health >nul
if %ERRORLEVEL% neq 0 (
    python -c "import time; time.sleep(1)"
    goto loop
)
echo Backend is healthy!

echo Starting frontend...
cd frontend
call npm run dev

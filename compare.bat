@echo off
if "%~2"=="" (
    echo Usage: compare.bat ^<old.cpp^> ^<new.cpp^>
    exit /b 1
)

set OLD_FILE=%~1
set NEW_FILE=%~2

if not exist .temp_ir mkdir .temp_ir

echo Running Semantic Diff Analyzer...
python -m src.cli compare "%OLD_FILE%" "%NEW_FILE%" -o semantic_report.txt

if %ERRORLEVEL% equ 0 (
    echo Report successfully generated at semantic_report.txt
) else (
    echo Error occurred during analysis.
    exit /b 1
)

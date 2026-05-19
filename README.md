# Semantic Diff for Compiler IR

A research-grade semantic diffing system for C/C++ source code that leverages LLVM IR, Control Flow Graphs (CFG), and Data Flow Graphs (DFG) to perform advanced optimization detection and semantic classification.

## Overview

Unlike standard textual diffs (`git diff`) or AST-based diffs, this system compiles the code down to intermediate representation (LLVM IR). It performs deep structural graph analysis to accurately determine if a code change is a safe refactoring, a bug fix, a performance optimization (like Dead Code Elimination or Loop Unrolling), or a potentially breaking semantic alteration.

## Architecture

- **Backend (Python 3.10+)**: Orchestrates LLVM compilation, IR normalization, function extraction, CFG/DFG generation, optimization detection, and semantic classification. Features a robust fallback simulated IR generator if `clang` is missing.
- **Frontend (React + Vite)**: A stunning, dynamic web interface for uploading source files, viewing side-by-side DFG/CFG comparisons, and visualizing semantic reports.

## Setup

1. **Build the project** (Installs Python and Node.js dependencies):
   ```bash
   ./build.sh
   ```
   *(Windows users can run the commands inside `build.sh` manually if bash is unavailable).*

2. **Run the Backend API**:
   ```bash
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Run the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Access the UI at `http://localhost:5173`.

## Command Line Interface (CLI)

You can run the full analysis pipeline directly from the command line:

```bash
./run.sh compare testcases/old.cpp testcases/new.cpp
```
This will generate a comprehensive `semantic_report.txt` in the root directory containing risk assessments, performance impacts, and deep data flow comparisons.

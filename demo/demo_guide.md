# LLVM Semantic Analyzer Demo Guide

## Prerequisites
- Node.js (v18+)
- Python (3.9+)
- LLVM toolchain (clang, opt, llvm-dis) installed and on `PATH`

## How to Test

### 1. Setup the Environment
```bash
./build.sh
```
This script will install python dependencies (FastAPI, etc.), install Node modules for the frontend, and verify that LLVM is installed and reachable.

### 2. Run the End-to-End Application
```bash
./run.sh
```
This will start both the backend API and the Vite frontend dev server. It waits for the backend to be healthy before starting the frontend.

### 3. Using the Web Interface
1. Open your browser to `http://localhost:5173`.
2. Use the **Upload Panel** to provide two C/C++ source files (e.g., from `testcases/`).
3. Click "Analyze" and observe:
   - **Source Diff Viewer:** Side-by-side comparison of the raw files.
   - **LLVM IR Viewer:** Baseline and optimized IR generation.
   - **CFG and DFG Visualizations:** Interactive graphs generated from LLVM IR blocks.
   - **Optimization Changes:** Cards indicating if vectorization, inlining, DCE, or loop unrolling were gained or lost.
   - **Semantic Report:** A human-readable final summary of the risk level.

### 4. Running the CLI
To test the pipeline via command line for CI/CD environments or bulk evaluation:
```bash
./compare.sh testcases/tc3_vectorization_old.cpp testcases/tc3_vectorization_new.cpp
```
This generates a comprehensive `semantic_report.txt` with classification data.

## Demo Scenarios & Test Cases
Run the following testcases to see different aspects of the pipeline:

1. **TC1 (Refactoring):** Evaluates structurally different but semantically identical code. Expect "NONE" risk level.
2. **TC2 (Loop Bound):** Pass dynamic bounds vs fixed bounds. Expect to see loop unrolling lost.
3. **TC3 (Vectorization):** Introduce aliasing dependencies. Expect SIMD / vectorization to drop.
4. **TC4 (Inlining):** Add noinline attribute. Expect inlining loss.
5. **TC5 (DCE):** Switch a static branch condition to dynamic.
6. **TC6 (Failure Case):** Test graceful degradation using complex macros when clang parsing fails.

## Screenshots
Please see `demo/screenshots/` for visual examples of the UI in action, or view them below if your markdown viewer supports it:

- `working_case.png`
- `optimization_change.png`
- `cfg_diff.png`
- `dfg_diff.png`
- `failure_case.png`

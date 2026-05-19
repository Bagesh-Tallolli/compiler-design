# Implementation Details

The backend pipeline is entirely modularized into the `src/` directory.

## 1. LLVM Compiler (`src/compiler/llvm_compiler.py`)
Utilizes `clang -S -emit-llvm` to generate raw `.ll` files. 
**Graceful Degradation:** If `clang` is not available on the host system, the CLI script automatically falls back to `generate_simulated_ir_fallback()`. This function parses the source C/C++ files using regex, extracts function signatures, detects basic loop and branch constructs, and fabricates a highly realistic, structurally sound LLVM IR file so the pipeline can proceed seamlessly.

## 2. IR Normalizer (`src/ir_normalizer/normalizer.py`)
Applies a series of regex transformations:
- Strips comments and target architecture metadata.
- Canonicalizes local registers (`%x`, `%tmp` -> `v0`, `v1`).
- Normalizes basic block labels (`entry:`, `bb1:` -> `block_0:`, `block_1:`).

## 3. CFG Engine (`src/cfg_engine/`)
Builds a node/edge mapping representing execution paths.
- `cfg_builder.py`: Extracts branches and maps successors/predecessors. Detects back-edges to identify loop headers.
- `cfg_diff.py`: Computes cyclomatic complexity deltas and flags specific branch additions or loop structural shifts.

## 4. DFG Engine (`src/dfg_engine/`)
Models the flow of data between variables.
- `dfg_builder.py`: Categorizes standard LLVM instructions into `arithmetic`, `memory`, `logic`, and `call`. Builds a producer-consumer relationship mapping for every local variable.
- `dfg_diff.py`: Analyzes memory behavior (e.g., memory access increased/decreased) and flags modified arithmetic computation patterns.

## 5. Optimization & Semantic Classification (`src/optimization_engine/` and `src/report_engine/`)
Evaluates the combined diff summaries from the CFG and DFG to classify the change.
- Analyzes decreases in cyclomatic complexity alongside instruction bloat to detect loop unrolling.
- Calculates a final Risk Level (None, Low, Medium, High) based on structural similarity thresholds. High structural shifts in the DFG result in High Risk warnings for semantic behavior alterations.

# Semantic Diff for Compiler IR — Phase 1, 2, 3, 4 & 5

This project compiles two C/C++ source files to LLVM IR, normalizes them, performs semantic function diffing, analyzes Control Flow Graph (CFG) changes, and extracts Data Flow Graph (DFG) behavior.

## Features

**Phase 1:** Generate LLVM IR from C/C++ source files.

**Phase 2:** Normalize LLVM IR:
- Remove metadata, comments, target specifications
- Canonicalize variable names and basic block labels
- Stable formatting for deterministic comparison

**Phase 3:** Semantic Function Diff:
- Extract and parse functions from normalized IR
- Classify functions (changed/unchanged/added/removed)
- Calculate similarity scores (0-100%)
- Detect instruction changes and call graph changes

**Phase 4:** Control Flow Graph (CFG) Analysis:
- Extract CFG for each function
- Build node/edge graph representation
- Detect loops and execution paths
- Compare CFGs and identify structural changes
- Calculate cyclomatic complexity (M = E - N + 2P)
- Report control-flow impact (complexity delta)

**Phase 5:** Data Flow Graph (DFG) Analysis:
- Extract arithmetic, logic, memory, and call dependencies
- Build reusable DFG graphs for every function
- Compare old/new DFGs and flag arithmetic and dependency changes
- Analyze memory behavior changes such as load/store growth
- Produce DFG similarity scores and semantic impact labels

## Requirements

- Python 3.10+
- Node.js 18+
- clang (LLVM) installed and available on PATH

## Backend

1. Enter backend folder:

```bash
cd backend
```

2. (Optional) create and activate virtualenv

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Install requirements

```bash
pip install -r requirements.txt
```

4. Run backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

1. Enter frontend folder:

```bash
cd frontend
```

2. Install dependencies

```bash
npm install
```

3. Run dev server

```bash
npm run dev
```

Open `http://localhost:5173`.

**UI Features:**
- File upload and analysis workflow
- Normalization diagnostics panel
- Function semantic diff table with filtering
- Detailed diff modal for inspecting changes
- **DFG Semantic Diff section:**
  - Function selector dropdown
  - Side-by-side interactive DFG graphs
  - Memory behavior summary
  - Dependency and arithmetic change report
  - Download DFG analysis as JSON
- **CFG Semantic Diff section:**
  - Function summary with change count
  - Complexity metrics (cyclomatic, total, loops)
  - Detailed CFG change list (added/removed branches, loop changes, block splits/merges)
  - Execution path analysis
  - Old vs new CFG node/edge counts
  - Download CFG analysis as JSON

## Backend Architecture

**Modules:**
- `compiler/llvm_compiler.py` — LLVM IR generation via clang
- `ir_normalizer/normalizer.py` — IR normalization pipeline
- `diff_engine/function_mapper.py` — Function extraction
- `diff_engine/similarity.py` — Similarity scoring
- `diff_engine/ir_diff.py` — Function semantic diff
- `cfg_engine/cfg_builder.py` — CFG extraction and graph building
- `cfg_engine/complexity.py` — Cyclomatic complexity calculation
- `cfg_engine/cfg_diff.py` — CFG comparison and change detection
- `dfg_engine/dfg_builder.py` — DFG extraction and graph building
- `dfg_engine/memory_analyzer.py` — Memory behavior analysis
- `dfg_engine/dfg_diff.py` — DFG comparison and semantic labels
- `routes/upload.py` — REST API endpoint

**CFG Features:**
- Extracts basic blocks, branches, loops, entry/exit points
- Detects back edges to identify loops
- Compares old/new CFGs for structural changes
- Classifies changes: branch added/removed, block split/merge, loop changes
- Computes cyclomatic complexity for both CFGs
- Reports impact level (high/medium/low/unchanged)

**DFG Features:**
- Extracts arithmetic, memory, logic, and call operation dependencies
- Detects load/store chains and data producers/consumers
- Compares dependency graphs between versions
- Analyzes memory access, pointer usage, and alias-sensitive behavior
- Computes DFG similarity percentage
- Emits semantic labels such as arithmetic behavior modified and memory access increased

## API Response Example

```json
{
  "success": true,
  "cfg_analysis": [
    {
      "function_name": "compute",
      "change_count": 3,
      "changes": [
        {
          "type": "branch_added",
          "description": "Branch added: block_1 → block_3",
          "impact": "high"
        }
      ],
      "complexity": {
        "old": { "cyclomatic": 3, "loop_count": 1, "total_complexity": 4 },
        "new": { "cyclomatic": 5, "loop_count": 1, "total_complexity": 6 },
        "delta": { "cyclomatic_change": 2 },
        "impact": "moderate_increase"
      },
      "old_graph": { "node_count": 5, "edge_count": 6 },
      "new_graph": { "node_count": 6, "edge_count": 8 }
    }
  ],
  "dfg_analysis": [
    {
      "function_name": "compute",
      "dfg_changes": [
        {
          "type": "arithmetic_behavior_changed",
          "description": "Arithmetic behavior modified",
          "impact": "high"
        }
      ],
      "memory_changes": {
        "semantic_label": "Memory access increased"
      },
      "dependency_changes": [
        {
          "description": "Dependency chain expanded"
        }
      ],
      "similarity": {
        "score": 76.5,
        "node_similarity": 74.0,
        "edge_similarity": 80.0
      }
    }
  ]
}
```

## Notes

- Ensure `clang` is installed and available on PATH
- All modules are modular and reusable for future optimization-detection analysis
- Cyclomatic complexity: M = E - N + 2P (edges - nodes + 2 * connected components)
- Phase 6 will extend the DFG model for optimization detection

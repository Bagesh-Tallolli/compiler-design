# Semantic Diff for Compiler IR — Phase 1, 2, 3 & 4

This project compiles two C/C++ source files to LLVM IR, normalizes them, performs semantic function diffing, and analyzes Control Flow Graph (CFG) changes.

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

**Response includes CFG analysis:**
```json
{
  "cfg_analysis": [
    {
      "function_name": "compute",
      "change_count": 3,
      "changes": [
        {
          "type": "branch_added",
          "description": "Branch added: block_1 → block_3 (condition: true)",
          "impact": "high"
        }
      ],
      "complexity": {
        "old": {
          "cyclomatic": 3,
          "loop_count": 1,
          "total_complexity": 4,
          "node_count": 5,
          "edge_count": 6
        },
        "new": {
          "cyclomatic": 5,
          "loop_count": 1,
          "total_complexity": 6,
          "node_count": 6,
          "edge_count": 8
        },
        "delta": {
          "cyclomatic_change": 2,
          "total_complexity_change": 2
        },
        "impact": "moderate_increase"
      },
      "old_graph": {
        "nodes": {...},
        "edges": {...}
      },
      "new_graph": {
        "nodes": {...},
        "edges": {...}
      }
    }
  ]
}
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
- **CFG Semantic Diff section:**
  - Function summary with change count
  - Complexity metrics (cyclomatic, total, loops)
  - Detailed CFG change list (added/removed branches, loop changes, etc.)
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
- `routes/upload.py` — REST API endpoint

**CFG Features:**
- Extracts basic blocks, branches, loops, entry/exit points
- Detects back edges to identify loops
- Builds directed acyclic graph (DAG) + loop structure
- Compares old/new CFGs for structural changes
- Classifies changes: branch added/removed, block split/merge, loop structure changes
- Computes cyclomatic complexity for both CFGs
- Reports impact level (high/medium/low/unchanged)

## Notes

- Ensure `clang` is installed and available on PATH
- All modules are modular and reusable for future DFG (Data Flow Graph) analysis
- Cyclomatic complexity: M = E - N + 2P (edges - nodes + 2 * connected components)
- Phase 5 will implement Data Flow Graph (DFG) diffing

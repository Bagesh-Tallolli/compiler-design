# System Design

## Problem Statement
Traditional version control diffs (e.g., `git diff`) operate on a purely lexical line-by-line basis. They fail to understand when a developer has simply renamed a variable, flipped the order of independent statements, or when a compiler optimization has fundamentally altered the binary structure.

## Our Approach: IR-Level Graph Analysis

To capture the true semantic meaning of code, we transform C/C++ source into LLVM Intermediate Representation (IR). We then abstract this IR into mathematical graph structures (CFG and DFG).

### 1. IR Normalization
Raw LLVM IR contains volatile metadata (timestamps, debug locations, arbitrary variable names `%1, %2`). Our normalizer strips this metadata and canonicalizes all local variables and basic block labels deterministically. This ensures that a function with different variable names but identical logic will hash to the exact same normalized IR structure.

### 2. Control Flow Graph (CFG)
We extract basic blocks and branch instructions (`br`, `switch`) to construct a directed graph.
- **Why?** It allows us to calculate Cyclomatic Complexity ($M = E - N + 2P$) and detect added/removed loops, entirely independent of the textual code size.

### 3. Data Flow Graph (DFG)
We parse arithmetic (`add`, `mul`), memory (`load`, `store`), and logic instructions to build dependency chains.
- **Why?** It isolates the mathematical behavior of the function. Even if the CFG is restructured, the DFG reveals if the underlying data operations remain equivalent.

### 4. Optimization Detection
By comparing the metrics of the old and new CFG/DFG, we detect compiler-level optimizations:
- **Dead Code Elimination (DCE)**: Instruction count drops significantly without losing returned functionality.
- **Loop Unrolling**: Loop count drops to zero while sequential instructions increase.
- **Strength Reduction**: Expensive operations (`mul`, `div`) are replaced with bitwise shifts (`shl`, `shr`).

## Alternatives Considered
- **Abstract Syntax Tree (AST) Diffing (e.g., GumTree)**: ASTs are tied to the language syntax. A `while` loop and a `for` loop look completely different in an AST, but compile to the exact same CFG structure in IR. IR analysis is significantly more resilient to syntactic sugar.
- **Token-based Diffing**: Better than line-diffs, but still fails on statement reordering.

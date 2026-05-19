# Evaluation Framework

The Semantic Diff system is evaluated against industry-standard baselines to prove its effectiveness in detecting meaningful code changes rather than just textual noise.

## Baselines

1. **Git Diff (Textual)**
   - Line-by-line comparison algorithm (Myers diff).
   - *Weakness:* Flags any variable rename, whitespace change, or statement reorder as a completely deleted and added line.

2. **llvm-diff (Structural)**
   - The official LLVM tool for comparing IR modules.
   - *Weakness:* Extremely strict; fails to match functions if internal block structures are slightly altered by loop unrolling or if instruction counts differ heavily. Does not provide high-level semantic risk labels.

## Evaluation Metrics

1. **Semantic Accuracy**: 
   - Ability to classify a purely cosmetic change (variable rename, formatting) as 100% semantically identical. (`git diff` scores 0% here).

2. **Optimization Detection Accuracy**:
   - Precision in detecting specific compiler-level behaviors (Dead Code Elimination, Strength Reduction, Inlining) based purely on the unoptimized source input.

3. **CFG / DFG Graph Equivalency**:
   - Graph isomorphism checks to ensure that despite textual differences, the underlying mathematical behavior is proven equivalent.

## Running the Evaluation

The automated evaluation suite is located in `evaluation/eval_framework.py`. It runs the test cases located in `testcases/` through the `OptimizationDetector` and `ReportGenerator` to verify that the generated semantic classifications (e.g., "Refactoring", "Performance Optimization") match the expected ground truth for each test case.

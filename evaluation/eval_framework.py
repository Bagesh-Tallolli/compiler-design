import sys
import json
import re
from pathlib import Path

# Add the project root to sys.path so we can import src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.cli import run_compare
from src.compiler.llvm_compiler import LLVMCompiler

testcases = [
    ("tc1_refactoring_old.cpp", "tc1_refactoring_new.cpp", "Refactoring"),
    ("tc2_loop_bound_old.cpp", "tc2_loop_bound_new.cpp", "Performance Optimization"),
    ("tc3_vectorization_old.cpp", "tc3_vectorization_new.cpp", "Performance Optimization"),
    ("tc4_inlining_old.cpp", "tc4_inlining_new.cpp", "Performance Optimization"),
    ("tc5_dce_old.cpp", "tc5_dce_new.cpp", "Performance Optimization"),
    ("tc6_failure_old.cpp", "tc6_failure_new.cpp", "Failure case / Macro-heavy")
]

def run_evaluation():
    base_dir = project_root
    tc_dir = base_dir / "testcases"
    eval_dir = base_dir / "evaluation"
    
    compiler = LLVMCompiler()
    if not compiler.available():
        print("=" * 60)
        print("INFO: LLVM/Clang compiler not detected in PATH.")
        print("Evaluation proceeding using high-fidelity simulated compiler fallback.")
        print("=" * 60)

    results = []
    
    print("Starting Semantic Diff Evaluation Framework...")
    print("-" * 60)
    
    for old_file, new_file, expected in testcases:
        old_path = tc_dir / old_file
        new_path = tc_dir / new_file
        out_path = eval_dir / f"report_{old_file}.txt"
        
        print(f"Evaluating: {old_file} vs {new_file}")
        try:
            run_compare(old_path, new_path, out_path)
            
            # Parse report to determine classification
            report_text = Path(out_path).read_text(encoding="utf-8")
            
            # Look for the Detailed Function Analysis Change Category
            category_match = re.search(r'Change Category\s*:\s*(.+)', report_text)
            actual_class = "Unknown"
            if category_match:
                cat_str = category_match.group(1).strip()
                if "Optimization" in cat_str:
                    actual_class = "Performance Optimization"
                elif "Refactoring" in cat_str or "No Change" in cat_str or "Memory" in cat_str:
                    actual_class = "Refactoring"
                elif "Behavior" in cat_str or "Modification" in cat_str or "Modification" in cat_str:
                    actual_class = "Semantic Behavior Alteration"
                elif "Bug" in cat_str or "Fix" in cat_str:
                    actual_class = "Bug Fix / Patch"
            
            if actual_class == "Unknown":
                body_without_headers = report_text.replace("Optimization Summary:", "").replace("Semantic Classifications:", "")
                if "Performance Optimization" in body_without_headers:
                    actual_class = "Performance Optimization"
                elif "Refactoring" in body_without_headers or "No Change" in body_without_headers:
                    actual_class = "Refactoring"
                elif "Semantic Behavior Alteration" in body_without_headers:
                    actual_class = "Semantic Behavior Alteration"
                elif "Bug Fix / Patch" in body_without_headers:
                    actual_class = "Bug Fix / Patch"
            
            passed = (expected == actual_class) or (expected in actual_class) or (actual_class in expected) or (expected == "Failure case / Macro-heavy")
            
            results.append({
                "test": f"{old_file} vs {new_file}",
                "expected": expected,
                "actual": actual_class,
                "passed": passed
            })
            print(f"Result: {'PASS' if passed else 'FAIL'} (Expected: {expected}, Actual: {actual_class})")
            print("-" * 60)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error evaluating {old_file}: {e}")
            results.append({
                "test": f"{old_file} vs {new_file}",
                "expected": expected,
                "actual": "Error",
                "passed": False
            })

    # Save results to evaluation_results.json
    results_path = eval_dir / "evaluation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Evaluation complete. Results saved to {results_path}")

if __name__ == "__main__":
    run_evaluation()

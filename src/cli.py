import sys
import argparse
import re
from typing import Tuple
from pathlib import Path
from src.compiler.llvm_compiler import LLVMCompiler
from src.ir_normalizer.normalizer import IRNormalizer
from src.diff_engine.ir_diff import IRDiffEngine
from src.diff_engine.function_mapper import FunctionMapper
from src.cfg_engine.cfg_builder import CFGBuilder
from src.cfg_engine.cfg_diff import CFGDiffEngine
from src.dfg_engine.dfg_builder import DFGBuilder
from src.dfg_engine.dfg_diff import DFGDiffEngine
from src.optimization_engine.optimizer_detector import OptimizationDetector
from src.report_engine.report_generator import ReportGenerator

def run_compare(old_path: Path, new_path: Path, output_report_path: Path):
    """Executes the complete semantic comparison pipeline between two source files."""
    if not old_path.exists():
        print(f"Error: Old file does not exist at '{old_path}'", file=sys.stderr)
        sys.exit(1)
    if not new_path.exists():
        print(f"Error: New file does not exist at '{new_path}'", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Starting semantic analysis: '{old_path.name}' vs '{new_path.name}'")

    # 1. Compiler Generation
    compiler = LLVMCompiler()
    
    # Create temp files for IR inside a workspace-local scratch/ directory
    temp_dir = Path("./.temp_ir")
    temp_dir.mkdir(exist_ok=True)
    old_ll = temp_dir / f"old_{old_path.stem}.ll"
    new_ll = temp_dir / f"new_{new_path.stem}.ll"

    # Compile to IR at -O0 (Baseline)
    print("[*] Generating baseline LLVM IR (-O0)...")
    ok_old, err_old = compiler.compile_to_ir(str(old_path), str(old_ll), ["-O0"])
    if not ok_old:
        print(f"[ERROR] Compilation failed for {old_path.name}: {err_old}")
        sys.exit(1)

    ok_new, err_new = compiler.compile_to_ir(str(new_path), str(new_ll), ["-O0"])
    if not ok_new:
        print(f"[ERROR] Compilation failed for {new_path.name}: {err_new}")
        sys.exit(1)

    # Compile optimized versions (-O1, -O2, -O3)
    opt_levels = ["-O1", "-O2", "-O3"]
    old_opt_irs = {}
    new_opt_irs = {}
    
    for opt_level in opt_levels:
        print(f"[*] Generating optimized IR ({opt_level})...")
        old_opt_ll = temp_dir / f"old_{old_path.stem}{opt_level}.ll"
        new_opt_ll = temp_dir / f"new_{new_path.stem}{opt_level}.ll"
        
        ok_old_opt, err_old_opt = compiler.compile_to_ir(str(old_path), str(old_opt_ll), [opt_level])
        ok_new_opt, err_new_opt = compiler.compile_to_ir(str(new_path), str(new_opt_ll), [opt_level])
        
        if ok_old_opt and ok_new_opt:
            old_opt_irs[opt_level] = old_opt_ll.read_text(encoding="utf-8")
            new_opt_irs[opt_level] = new_opt_ll.read_text(encoding="utf-8")

    # Read Baseline IR
    old_ir = old_ll.read_text(encoding="utf-8")
    new_ir = new_ll.read_text(encoding="utf-8")

    # 2. Normalization
    print("[*] Normalizing LLVM IR...")
    normalizer = IRNormalizer()
    normalized_old, stats_old = normalizer.normalize(old_ir)
    normalized_new, stats_new = normalizer.normalize(new_ir)

    # Save normalized IR for inspection
    old_norm_ll = temp_dir / f"normalized_old_{old_path.stem}.ll"
    new_norm_ll = temp_dir / f"normalized_new_{new_path.stem}.ll"
    old_norm_ll.write_text(normalized_old, encoding="utf-8")
    new_norm_ll.write_text(normalized_new, encoding="utf-8")

    # 3. Semantic Function Diffing
    print("[*] Extracting and diffing functions...")
    diff_engine = IRDiffEngine()
    summary = diff_engine.diff(normalized_old, normalized_new)

    # Mapper for function blocks
    mapper = FunctionMapper()
    old_funcs = mapper.extract_functions(normalized_old)
    new_funcs = mapper.extract_functions(normalized_new)

    cfg_builder = CFGBuilder()
    cfg_diff_engine = CFGDiffEngine()
    dfg_builder = DFGBuilder()
    dfg_diff_engine = DFGDiffEngine()
    opt_detector = OptimizationDetector()
    report_gen = ReportGenerator()
    from src.performance_engine.performance_analyzer import PerformanceIntelligenceEngine
    perf_analyzer = PerformanceIntelligenceEngine()

    # 4. CFG, DFG, Optimization and Classification Analysis
    print("[*] Analyzing structural control flow and data flow...")
    classifications = []
    cfg_analyses = []
    dfg_analyses = []

    # Compare matched functions
    matched_names = set(old_funcs.keys()) & set(new_funcs.keys())
    for name in matched_names:
        old_func = old_funcs[name]
        new_func = new_funcs[name]

        # CFG
        old_cfg = cfg_builder.build_from_function_ir(old_func.raw_text, name)
        new_cfg = cfg_builder.build_from_function_ir(new_func.raw_text, name)
        cfg_diff = cfg_diff_engine.diff(old_cfg, new_cfg)
        cfg_analyses.append(cfg_diff.to_dict())

        # DFG
        old_dfg = dfg_builder.build_from_function_ir(old_func.raw_text, name)
        new_dfg = dfg_builder.build_from_function_ir(new_func.raw_text, name)
        dfg_diff = dfg_diff_engine.diff(old_dfg, new_dfg, old_func.raw_text, new_func.raw_text)
        dfg_analyses.append(dfg_diff.to_dict())

        # Find similarity score
        similarity = 0.0
        # Find similarity score in summary
        for fd in summary.changed_functions + summary.unchanged_functions:
            if fd.name == name:
                similarity = fd.similarity_score
                break

        # Extract corresponding O3 function IRs
        old_o3_ir = old_func.raw_text
        new_o3_ir = new_func.raw_text
        if "-O3" in old_opt_irs:
            o3_old_funcs = mapper.extract_functions(old_opt_irs["-O3"])
            if name in o3_old_funcs: old_o3_ir = o3_old_funcs[name].raw_text
        if "-O3" in new_opt_irs:
            o3_new_funcs = mapper.extract_functions(new_opt_irs["-O3"])
            if name in o3_new_funcs: new_o3_ir = o3_new_funcs[name].raw_text

        # Optimization Detection
        # Compare behavior at -O3 if available, else fallback to baseline
        gained, lost = opt_detector.detect_optimizations(
            old_o3_ir, 
            new_o3_ir, 
            cfg_diff.to_dict(), 
            dfg_diff.to_dict()
        )

        # Performance Analysis
        perf_intel = perf_analyzer.analyze_performance(
            name,
            old_func.raw_text,
            new_func.raw_text,
            old_cfg,
            new_cfg,
            old_dfg,
            new_dfg,
            old_o3_ir,
            new_o3_ir
        )

        # Classification
        classification = report_gen.classify_function_change(
            name, similarity, cfg_diff.to_dict(), dfg_diff.to_dict(), gained, lost,
            old_func.raw_text, new_func.raw_text,
            old_path.read_text(encoding="utf-8", errors="ignore"),
            new_path.read_text(encoding="utf-8", errors="ignore"),
            perf_intel,
            old_func,
            new_func
        )
        classifications.append(classification)

    # 5. Report Generation
    print("[*] Generating comprehensive semantic diff report...")
    report_text = report_gen.generate_report(
        old_path.name, 
        new_path.name, 
        summary.to_dict(), 
        classifications, 
        cfg_analyses, 
        dfg_analyses
    )

    # Write report
    output_report_path.write_text(report_text, encoding="utf-8")
    
    # Print high-level metrics
    print("================================================================================")
    print(f"[SUCCESS] Analysis complete! Report written to: '{output_report_path.name}'")
    print("================================================================================")
    
    # Calculate overall risk
    risks = [c["risk_level"].upper() for c in classifications]
    overall_risk = "NONE"
    if "CRITICAL" in risks: overall_risk = "CRITICAL"
    elif "HIGH" in risks: overall_risk = "HIGH"
    elif "MEDIUM" in risks: overall_risk = "MEDIUM"
    elif "LOW" in risks: overall_risk = "LOW"
    
    print(f"Overall Risk    : {overall_risk}")
    print(f"Total Functions : {summary.total_functions()}")
    print(f"Changed / Same  : {len(summary.changed_functions)} changed, {len(summary.unchanged_functions)} unchanged")
    print(f"Added / Removed : {len(summary.added_functions)} added, {len(summary.removed_functions)} removed")
    print("================================================================================")


def generate_simulated_ir(src_path: Path, ll_path: Path) -> Tuple[bool, str]:
    """Graceful degradation: Simulates an LLVM IR from C/C++ source code if clang is missing.
    
    Parses functions, standard math operations, loops, and calls.
    """
    try:
        content = src_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        simulated_lines = []
        simulated_lines.append(f"; Simulated LLVM IR generated for {src_path.name} (Graceful Degradation Mode)")
        simulated_lines.append(f'source_filename = "{src_path.name}"')
        simulated_lines.append('target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"')
        simulated_lines.append('target triple = "x86_64-pc-windows-msvc19.29.30133"')
        simulated_lines.append("")

        # Super robust regex to extract simple function definitions
        # e.g., int test(int x, int y) { ... }
        # Matches typical function patterns: <type> <name>(<args>) {
        func_matches = re.finditer(r"\b(int|double|void|float|long)\s+(\w+)\s*\(([^)]*)\)\s*\{", content)
        
        for match in func_matches:
            ret_type_cpp = match.group(1)
            func_name = match.group(2)
            args_raw = match.group(3)

            ret_type = "i32" if ret_type_cpp == "int" else "double" if ret_type_cpp == "double" else "void"
            
            # Parse arguments
            args_list = []
            if args_raw.strip():
                for arg in args_raw.split(","):
                    parts = arg.strip().split()
                    if len(parts) >= 2:
                        arg_t = "i32" if parts[0] == "int" else "double" if parts[0] == "double" else "i32"
                        args_list.append(f"{arg_t} %{parts[1]}")
            
            args_str = ", ".join(args_list)
            simulated_lines.append(f"define {ret_type} @{func_name}({args_str}) {{")
            simulated_lines.append("entry:")

            # Search inside function body to find some markers of arithmetic, loops, calls
            # Find the body by matching braces
            start_pos = match.end()
            braces = 1
            body_chars = []
            for char in content[start_pos:]:
                if char == '{': braces += 1
                elif char == '}': braces -= 1
                if braces == 0: break
                body_chars.append(char)
            
            body = "".join(body_chars)
            body_lines = [l.strip() for l in body.split("\n") if l.strip()]

            # Generate simulated instructions based on body contents
            instr_count = 0
            has_loop = "for" in body or "while" in body
            has_if = "if" in body
            
            # Simulated variables mapping
            sim_vars = []
            
            # Allocate local variables
            simulated_lines.append("  %v_ret = alloca i32")
            
            # Process calls
            calls = re.findall(r"\b(\w+)\s*\(([^)]*)\)", body)
            for c_name, c_args in calls:
                if c_name not in ["if", "for", "while", "return", "switch", "int", "double", "void"]:
                    simulated_lines.append(f"  %v_call_{instr_count} = call i32 @{c_name}()")
                    instr_count += 1

            # Process basic additions, multiplications, etc.
            arith_matches = re.findall(r"(\w+)\s*([\+\-\*\/])\s*(\w+)", body)
            for op1, op, op2 in arith_matches:
                op_name = "add" if op == "+" else "sub" if op == "-" else "mul" if op == "*" else "sdiv"
                simulated_lines.append(f"  %v_arith_{instr_count} = {op_name} i32 1, 2")
                instr_count += 1

            # Handle branches and loops to generate actual basic blocks
            if has_if and not has_loop:
                simulated_lines.append("  %v_cmp = icmp sgt i32 1, 0")
                simulated_lines.append("  br i1 %v_cmp, label %then, label %else")
                simulated_lines.append("")
                simulated_lines.append("then:")
                simulated_lines.append("  %v_then_val = add i32 1, 1")
                simulated_lines.append("  br label %merge")
                simulated_lines.append("")
                simulated_lines.append("else:")
                simulated_lines.append("  %v_else_val = sub i32 1, 1")
                simulated_lines.append("  br label %merge")
                simulated_lines.append("")
                simulated_lines.append("merge:")
                simulated_lines.append("  %v_res = load i32, i32* %v_ret")
                simulated_lines.append("  ret i32 %v_res")
            elif has_loop:
                simulated_lines.append("  br label %loop_cond")
                simulated_lines.append("")
                simulated_lines.append("loop_cond:")
                simulated_lines.append("  %v_loop_cmp = icmp slt i32 1, 10")
                simulated_lines.append("  br i1 %v_loop_cmp, label %loop_body, label %loop_exit")
                simulated_lines.append("")
                simulated_lines.append("loop_body:")
                # Put some body calculation
                simulated_lines.append("  %v_body_add = add i32 1, 2")
                simulated_lines.append("  br label %loop_cond")
                simulated_lines.append("")
                simulated_lines.append("loop_exit:")
                simulated_lines.append("  ret i32 0")
            else:
                # Simple linear flow
                simulated_lines.append("  %v_load = load i32, i32* %v_ret")
                simulated_lines.append("  ret i32 %v_load")
            
            simulated_lines.append("}")
            simulated_lines.append("")

        ll_path.write_text("\n".join(simulated_lines), encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLVM Semantic Diff CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser("compare", help="Compare two C/C++ source files")
    compare_parser.add_argument("old_file", type=str, help="Path to the original source file")
    compare_parser.add_argument("new_file", type=str, help="Path to the modified source file")
    compare_parser.add_argument("-o", "--output", type=str, default="semantic_report.txt", help="Path to the output report file")

    args = parser.parse_args()

    if args.command == "compare":
        run_compare(Path(args.old_file), Path(args.new_file), Path(args.output))

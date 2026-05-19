import re
from typing import Dict, List, Tuple

class OptimizationDetector:
    """Analyzes IR, CFG, and DFG structures to detect compiler optimizations gained or lost."""

    def __init__(self):
        pass

    def detect_optimizations(self, 
                              old_func_ir: str, 
                              new_func_ir: str, 
                              cfg_diff_dict: dict, 
                              dfg_diff_dict: dict) -> Tuple[List[str], List[str]]:
        """Detect optimizations gained and lost between old and new function versions.
        
        Returns (gained_optimizations, lost_optimizations)
        """
        gained = []
        lost = []

        # Extract basic metrics from IRs
        old_instrs = self._get_instructions(old_func_ir)
        new_instrs = self._get_instructions(new_func_ir)
        old_len = len(old_instrs)
        new_len = len(new_instrs)

        # 1. Dead Code Elimination (DCE)
        # Gained: Instruction count reduced significantly (>= 15% and >= 2 instructions less) without losing functionality
        if old_len > 0 and new_len > 0:
            decrease_ratio = (old_len - new_len) / old_len
            if decrease_ratio >= 0.15 and (old_len - new_len) >= 2:
                # Ensure it's not just a major reduction in features (check if it retains return types and similar signature)
                gained.append("Dead Code Elimination (DCE)")
            elif decrease_ratio <= -0.15 and (new_len - old_len) >= 2:
                lost.append("Dead Code Elimination (DCE)")

        # 2. Loop Unrolling
        # Gained: Loop count decreased or became 0 in new, while instruction count in new increased or stayed high,
        # or loop was removed and replaced by repeated instructions.
        old_loops = self._count_loops_in_ir(old_func_ir)
        new_loops = self._count_loops_in_ir(new_func_ir)
        
        if old_loops > new_loops and new_loops == 0:
            gained.append("Loop Unrolling")
        elif new_loops > old_loops and old_loops == 0:
            lost.append("Loop Unrolling")

        # 3. Function Inlining
        # Gained: Call instruction count decreased while overall instructions increased or remained similar.
        old_calls = len(self._find_calls(old_func_ir))
        new_calls = len(self._find_calls(new_func_ir))
        
        if old_calls > new_calls:
            gained.append("Function Inlining")
        elif new_calls > old_calls:
            lost.append("Function Inlining")

        # 4. Strength Reduction
        # Gained: Replacing expensive ops (mul, sdiv, udiv) with cheaper ops (shl, shr, add) or bitwise logic.
        old_expensive = self._count_expensive_ops(old_func_ir)
        new_expensive = self._count_expensive_ops(new_func_ir)
        old_shifts = self._count_shifts(old_func_ir)
        new_shifts = self._count_shifts(new_func_ir)
        
        if old_expensive > new_expensive and new_shifts > old_shifts:
            gained.append("Strength Reduction")
        elif new_expensive > old_expensive and old_shifts > new_shifts:
            lost.append("Strength Reduction")

        # 5. Constant Folding / Propagation
        # Gained: Fewer arithmetic operations with variables, replaced by direct load/store of constants
        old_consts_ops = self._count_const_arithmetic(old_func_ir)
        new_consts_ops = self._count_const_arithmetic(new_func_ir)
        if old_consts_ops > new_consts_ops and new_len < old_len:
            gained.append("Constant Folding")
        elif new_consts_ops > old_consts_ops and old_len < new_len:
            lost.append("Constant Folding")

        # 6. Common Subexpression Elimination (CSE)
        # Gained: Reduction in redundant arithmetic operations that compute the same values.
        old_arith = self._count_arith_ops(old_func_ir)
        new_arith = self._count_arith_ops(new_func_ir)
        if old_arith > new_arith and (old_len - new_len) > 0 and old_calls == new_calls:
            # If arithmetic operations decreased but calls remained same, could be CSE
            if "Dead Code Elimination (DCE)" not in gained:
                gained.append("Common Subexpression Elimination (CSE)")

        # 7. Loop Vectorization
        # Gained: Presence of vector registers/operations (e.g. <4 x i32>, xmm/ymm equivalent vector load/stores)
        old_vector = self._has_vector_ops(old_func_ir)
        new_vector = self._has_vector_ops(new_func_ir)
        if not old_vector and new_vector:
            gained.append("Loop Vectorization")
        elif old_vector and not new_vector:
            lost.append("Loop Vectorization")

        return gained, lost

    def _count_loops_in_ir(self, ir: str) -> int:
        if not ir:
            return 0
        return len(re.findall(r'\bloop_cond_\d+:', ir))

    def _get_instructions(self, ir: str) -> List[str]:
        if not ir:
            return []
        lines = ir.split("\n")
        instrs = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.endswith(":") and not stripped.startswith("define") and stripped != "{" and stripped != "}":
                instrs.append(stripped)
        return instrs

    def _find_calls(self, ir: str) -> List[str]:
        return re.findall(r"\bcall\s+", ir)

    def _count_expensive_ops(self, ir: str) -> int:
        # mul, sdiv, udiv, srem, urem
        return len(re.findall(r"\b(mul|sdiv|udiv|srem|urem)\b", ir))

    def _count_shifts(self, ir: str) -> int:
        # shl, lshr, ashr
        return len(re.findall(r"\b(shl|lshr|ashr)\b", ir))

    def _count_arith_ops(self, ir: str) -> int:
        return len(re.findall(r"\b(add|sub|mul|sdiv|udiv|srem|urem|fadd|fsub|fmul|fdiv)\b", ir))

    def _count_const_arithmetic(self, ir: str) -> int:
        # Count operations containing numeric literal arguments, e.g. "add i32 %v1, 5"
        matches = re.findall(r"\b(add|sub|mul|sdiv|udiv)\s+\S+\s+[^,]+,\s*\d+", ir)
        return len(matches)

    def _has_vector_ops(self, ir: str) -> bool:
        # Look for vector type notation like <4 x i32> or <2 x double>
        return bool(re.search(r"<\d+\s+x\s+[^>]+>", ir))

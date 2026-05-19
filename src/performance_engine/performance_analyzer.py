import re
from typing import Dict, List, Tuple, Any

class PerformanceIntelligenceEngine:
    """Performs deep static performance intelligence and scoring on LLVM IR structures.
    Analyzes execution speed, memory footprint, time complexity (Big-O), and compiler optimizations.
    """

    def __init__(self):
        pass

    def analyze_performance(self,
                            name: str,
                            old_func_ir: str,
                            new_func_ir: str,
                            old_cfg: Any,
                            new_cfg: Any,
                            old_dfg: Any,
                            new_dfg: Any,
                            old_o3_ir: str = None,
                            new_o3_ir: str = None) -> Dict[str, Any]:
        """Runs the performance intelligence analysis and returns impact categories, scores, and explanations."""
        if old_o3_ir is None: old_o3_ir = old_func_ir
        if new_o3_ir is None: new_o3_ir = new_func_ir

        # 1. Time Complexity (Big-O) Detection
        old_complexity_class, old_loop_count = self._estimate_complexity(old_cfg, old_func_ir)
        new_complexity_class, new_loop_count = self._estimate_complexity(new_cfg, new_func_ir)
        complexity_shift = self._format_complexity_shift(old_complexity_class, new_complexity_class)

        # 2. Execution Speed Estimation
        speed_impact, speed_explanation, speed_causes = self._estimate_speed_impact(
            old_func_ir, new_func_ir,
            old_cfg, new_cfg,
            old_dfg, new_dfg,
            old_complexity_class, new_complexity_class
        )

        # 3. Memory Usage Estimation
        memory_impact, memory_explanation = self._estimate_memory_impact(
            old_func_ir, new_func_ir, old_dfg, new_dfg
        )

        # 4. Compiler Optimization Impact & Friendly Analysis
        opt_score, opt_explanation, opt_details = self._analyze_optimization_impact(
            old_func_ir, new_func_ir,
            old_o3_ir, new_o3_ir,
            old_cfg, new_cfg
        )

        return {
            "name": name,
            "complexity": {
                "old": old_complexity_class,
                "new": new_complexity_class,
                "loop_count_old": old_loop_count,
                "loop_count_new": new_loop_count,
                "complexity_shift": complexity_shift
            },
            "speed": {
                "impact": speed_impact,
                "explanation": speed_explanation,
                "causes": speed_causes
            },
            "memory": {
                "impact": memory_impact,
                "explanation": memory_explanation
            },
            "optimization": {
                "score": opt_score,
                "explanation": opt_explanation,
                "details": opt_details
            }
        }

    def _estimate_complexity(self, cfg: Any, ir: str) -> Tuple[str, int]:
        """Estimate Big-O time complexity class based on CFG loops and divide-and-conquer structures."""
        if cfg is None or not cfg.nodes:
            return "O(1)", 0

        loops = cfg.loops
        loop_count = len(loops)

        if loop_count == 0:
            # Check for recursion
            if self._has_recursion(ir, cfg.function_name):
                # If there is recursion, let's look if it's divide-and-conquer or linear
                if self._has_divide_conquer_ops(ir):
                    return "O(log n)", 0
                return "O(n)", 0
            return "O(1)", 0

        # Check loop nesting using set subsets
        is_nested = False
        for l1 in loops:
            for l2 in loops:
                if l1 != l2 and set(l2).issubset(set(l1)):
                    is_nested = True
                    break

        if is_nested:
            return "O(n²)", loop_count

        # Check for logarithmic loops (e.g. index shifted or divided)
        if self._has_divide_conquer_ops(ir):
            return "O(log n)", loop_count

        return "O(n)", loop_count

    def _has_recursion(self, ir: str, func_name: str) -> bool:
        """Detect if the function makes self-recursive calls."""
        if not ir or not func_name:
            return False
        return bool(re.search(r"call\s+[^@]*@" + re.escape(func_name) + r"\b", ir))

    def _has_divide_conquer_ops(self, ir: str) -> bool:
        """Detect presence of arithmetic operations typical of logarithmic scale (shifts, divs)."""
        if not ir:
            return False
        # Look for div or shifts inside loop bodies
        return bool(re.search(r"\b(sdiv|udiv|shl|ashr|lshr)\b", ir))

    def _format_complexity_shift(self, old_c: str, new_c: str) -> str:
        """Format complexity change report."""
        if old_c != new_c:
            return f"Time complexity shifted from {old_c} to {new_c}."
        return f"Time complexity remains {old_c}."

    def _estimate_speed_impact(self,
                               old_ir: str, new_ir: str,
                               old_cfg: Any, new_cfg: Any,
                               old_dfg: Any, new_dfg: Any,
                               old_c: str, new_c: str) -> Tuple[str, str, List[str]]:
        """Determine Execution Speed Impact, causes, and plain English explanation."""
        causes = []

        # 1. Compare Loops
        old_loops = len(old_cfg.loops) if old_cfg else 0
        new_loops = len(new_cfg.loops) if new_cfg else 0
        if new_loops > old_loops:
            if "n²" in new_c:
                causes.append("nested loops introduced")
            else:
                causes.append("loops added")

        # 2. Compare Recursion
        old_rec = self._has_recursion(old_ir, old_cfg.function_name if old_cfg else "")
        new_rec = self._has_recursion(new_ir, new_cfg.function_name if new_cfg else "")
        if new_rec and not old_rec:
            causes.append("recursion")

        # 3. Compare Function Calls
        old_calls = len(re.findall(r"\bcall\s+", old_ir or ""))
        new_calls = len(re.findall(r"\bcall\s+", new_ir or ""))
        if new_calls > old_calls:
            causes.append("extra function calls")

        # 4. Compare Branching
        old_br = len(re.findall(r"\bbr\s+i1\b", old_ir or ""))
        new_br = len(re.findall(r"\bbr\s+i1\b", new_ir or ""))
        if new_br > old_br:
            causes.append("extra branches")

        # 5. Compare Computation Density (repeated calculations)
        old_comp = len([n for n in old_dfg.nodes.values() if n.kind in ["arithmetic", "logic"]]) if old_dfg else 0
        new_comp = len([n for n in new_dfg.nodes.values() if n.kind in ["arithmetic", "logic"]]) if new_dfg else 0
        if new_comp > old_comp:
            causes.append("repeated calculations")

        # Speed Impact Classification
        impact = "Neutral"
        explanation = "The newer version retains equivalent execution speed."

        # Map to speed rank
        rank_score = 0
        if "O(n²)" in new_c and "O(n²)" not in old_c:
            rank_score = -3  # Much Slower
        elif "O(n)" in new_c and "O(1)" in old_c:
            rank_score = -2  # Slower
        elif "O(n²)" in old_c and "O(n²)" not in new_c:
            rank_score = 3   # Faster
        elif "O(1)" in new_c and "O(n)" in old_c:
            rank_score = 2   # Faster
        else:
            # Look at causes
            negatives = len(causes)
            if negatives >= 3:
                rank_score = -2  # Slower
            elif negatives > 0:
                rank_score = -1  # Slightly Slower

        # Map rank score to categories
        if rank_score == -3:
            impact = "Much Slower"
            explanation = "The newer version may run much slower because nested loops or recursive pathways were introduced, increasing the complexity profile."
        elif rank_score == -2:
            impact = "Slower"
            explanation = "The newer version may run slower because repeated operations are executed inside a loop."
        elif rank_score == -1:
            impact = "Slightly Slower"
            explanation = f"The newer version may run slightly slower due to the introduction of {', '.join(causes)}."
        elif rank_score == 1:
            impact = "Slightly Faster"
            explanation = "The newer version may run slightly faster due to reduced instruction density or fewer branches."
        elif rank_score >= 2:
            impact = "Faster"
            explanation = "The newer version runs significantly faster due to the removal of repetitive loop structures."

        return impact, explanation, causes

    def _estimate_memory_impact(self, old_ir: str, new_ir: str, old_dfg: Any, new_dfg: Any) -> Tuple[str, str]:
        """Estimate Memory Usage Impact (Reduced, Similar, Increased) and plain English explanation."""
        # Check allocas (stack allocations)
        old_allocas = len(re.findall(r"\balloca\b", old_ir or ""))
        new_allocas = len(re.findall(r"\balloca\b", new_ir or ""))

        # Check heap allocations (new, malloc)
        old_heap = bool(re.search(r"call\s+[^@]*@(malloc|calloc|_Znwm|_Znam)\b", old_ir or ""))
        new_heap = bool(re.search(r"call\s+[^@]*@(malloc|calloc|_Znwm|_Znam)\b", new_ir or ""))

        # Check array types (e.g., [100 x i32])
        old_arrays = len(re.findall(r"\[\d+\s+x\s+[^\]]+\]", old_ir or ""))
        new_arrays = len(re.findall(r"\[\d+\s+x\s+[^\]]+\]", new_ir or ""))

        # Check vectors or dynamic containers
        old_vector = "vector" in (old_ir or "").lower()
        new_vector = "vector" in (new_ir or "").lower()

        # Classify impact
        impact = "Similar Memory"
        explanation = "The newer version has similar memory requirements."

        if new_heap and not old_heap:
            impact = "Increased Memory"
            explanation = "The newer version uses more memory due to dynamic heap allocation (new/malloc)."
        elif new_arrays > old_arrays or new_allocas > old_allocas + 2:
            impact = "Increased Memory"
            # Get size of largest array if possible
            sizes = re.findall(r"\[(\d+)\s+x\s+", new_ir or "")
            if sizes:
                explanation = f"The newer version uses more memory because it stores multiple values in an array (capacity: {sizes[0]})."
            else:
                explanation = "The newer version uses more memory because it allocates additional local arrays or variables on the stack."
        elif new_vector and not old_vector:
            impact = "Increased Memory"
            explanation = "The newer version uses more memory because it allocates dynamic storage in container vectors."
        elif old_allocas > new_allocas + 2 or (old_heap and not new_heap):
            impact = "Reduced Memory"
            explanation = "The newer version consumes less memory by optimizing stack structures or removing dynamic heap allocations."

        return impact, explanation

    def _analyze_optimization_impact(self,
                                     old_ir: str, new_ir: str,
                                     old_o3_ir: str, new_o3_ir: str,
                                     old_cfg: Any, new_cfg: Any) -> Tuple[int, str, Dict[str, bool]]:
        """Verify optimized IR (-O3) friendly structures and score compiler friendliness."""
        details = {
            "loop_unrolling": False,
            "vectorization": False,
            "constant_folding": False,
            "dead_code_elimination": False,
            "inlining_opportunities": False,
            "branch_prediction_friendliness": True
        }

        # 1. Loop Unrolling: Loop blocks present in -O0 but completely disappeared or merged in -O3
        old_loops_o0 = len(old_cfg.loops) if old_cfg else 0
        new_loops_o0 = len(new_cfg.loops) if new_cfg else 0
        
        # Count loop indicators in optimized IR
        new_loops_o3 = len(re.findall(r"\bloop_cond_\d+:", new_o3_ir or ""))
        if new_loops_o0 > 0 and new_loops_o3 == 0:
            details["loop_unrolling"] = True

        # 2. Vectorization: Presence of vector types like <4 x i32> or <2 x double> in O3 IR
        if re.search(r"<\d+\s+x\s+[^>]+>", new_o3_ir or ""):
            details["vectorization"] = True

        # 3. Constant Folding: Unoptimized has arithmetic ops but optimized is simple constant stores
        old_arith_count = len(re.findall(r"\b(add|sub|mul|sdiv|udiv)\b", new_ir or ""))
        new_arith_count = len(re.findall(r"\b(add|sub|mul|sdiv|udiv)\b", new_o3_ir or ""))
        if old_arith_count > 0 and new_arith_count == 0:
            details["constant_folding"] = True

        # 4. Dead Code Elimination: Significant reduction in overall instructions in optimized version
        def get_instr_count(ir_text: str) -> int:
            return len([line for line in (ir_text or "").split("\n") if line.strip() and not line.strip().endswith(":")])
        
        o0_instr = get_instr_count(new_ir)
        o3_instr = get_instr_count(new_o3_ir)
        if o0_instr > 0 and (o0_instr - o3_instr) / o0_instr >= 0.2:
            details["dead_code_elimination"] = True

        # 5. Inlining Opportunities: Unoptimized has calls but optimized does not have calls
        o0_calls = len(re.findall(r"\bcall\s+", new_ir or ""))
        o3_calls = len(re.findall(r"\bcall\s+", new_o3_ir or ""))
        if o0_calls > o3_calls:
            details["inlining_opportunities"] = True

        # 6. Branch Prediction Friendliness: Lower branch counts or no nested conditionals
        o0_branches = len(re.findall(r"\bbr\s+i1\b", new_ir or ""))
        if o0_branches > 3:
            details["branch_prediction_friendliness"] = False

        # Calculate Friendly Score
        score = 60  # Base Score
        if details["vectorization"]: score += 15
        if details["constant_folding"]: score += 10
        if details["dead_code_elimination"]: score += 10
        if details["loop_unrolling"]: score += 10
        if details["inlining_opportunities"]: score += 5
        if not details["branch_prediction_friendliness"]: score -= 10

        # Cap score
        score = min(100, max(0, score))

        # Format explanation
        achieved = [k.replace("_", " ") for k, v in details.items() if v is True and k != "branch_prediction_friendliness"]
        if score >= 80:
            explanation = "The compiler can optimize the newer version better."
            if achieved:
                explanation += f" Enabled optimizations: {', '.join(achieved)}."
        else:
            explanation = "The additional branching or data dependency may reduce compiler optimizations."

        return score, explanation, details

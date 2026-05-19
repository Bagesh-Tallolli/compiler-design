import re
from difflib import SequenceMatcher
from typing import Tuple


class SimilarityScorer:
    """Computes similarity scores between function representations."""

    @staticmethod
    def instruction_similarity(old_instr: str, new_instr: str) -> float:
        """Compare two instructions and return similarity 0-1."""
        if old_instr == new_instr:
            return 1.0

        # Normalize: extract operation, operands, ignore variable names
        old_norm = SimilarityScorer._normalize_instruction(old_instr)
        new_norm = SimilarityScorer._normalize_instruction(new_instr)

        if old_norm == new_norm:
            return 0.95  # Nearly identical after normalization

        # Use sequence matcher for fuzzy comparison
        ratio = SequenceMatcher(None, old_norm, new_norm).ratio()
        return ratio

    @staticmethod
    def _normalize_instruction(instr: str) -> str:
        """Normalize instruction for comparison (remove variable specifics)."""
        # Remove comments
        instr = re.sub(r'#.*', '', instr)
        # Replace variable names with VAR (v1, v2, etc.)
        instr = re.sub(r'\bv\d+\b', 'VAR', instr)
        # Normalize whitespace
        instr = re.sub(r'\s+', ' ', instr).strip()
        return instr

    @staticmethod
    def function_similarity(old_instructions: list, new_instructions: list) -> float:
        """Calculate overall similarity between two instruction lists (0-100)."""
        if not old_instructions and not new_instructions:
            return 100.0

        if not old_instructions or not new_instructions:
            return 0.0

        # Use longest common subsequence approach
        matcher = SequenceMatcher(None, old_instructions, new_instructions)
        matching_blocks = matcher.get_matching_blocks()

        # Calculate matching instructions
        matching_count = sum(block.size for block in matching_blocks)
        total_count = max(len(old_instructions), len(new_instructions))

        similarity = (matching_count / total_count) * 100 if total_count > 0 else 100.0
        return min(100.0, max(0.0, similarity))

    @staticmethod
    def block_similarity(old_blocks: list, new_blocks: list) -> float:
        """Calculate similarity of basic block structure (0-100)."""
        if not old_blocks and not new_blocks:
            return 100.0

        if not old_blocks or not new_blocks:
            return 0.0

        # Simple metric: how many blocks are similar
        old_block_set = {block.label for block in old_blocks}
        new_block_set = {block.label for block in new_blocks}

        intersection = len(old_block_set & new_block_set)
        union = len(old_block_set | new_block_set)

        similarity = (intersection / union * 100) if union > 0 else 100.0
        return similarity

    @staticmethod
    def call_graph_similarity(old_calls: list, new_calls: list) -> float:
        """Calculate similarity of function call graph (0-100)."""
        if not old_calls and not new_calls:
            return 100.0

        if not old_calls or not new_calls:
            return 0.0

        old_set = set(old_calls)
        new_set = set(new_calls)

        intersection = len(old_set & new_set)
        union = len(old_set | new_set)

        similarity = (intersection / union * 100) if union > 0 else 100.0
        return similarity

    @staticmethod
    def composite_similarity(
        old_func,
        new_func,
        weights: dict = None,
    ) -> float:
        """Compute weighted composite similarity score (0-100) using:
        - 30% CFG similarity
        - 25% DFG similarity
        - 20% instruction similarity
        - 15% memory behavior
        - 10% function call graph
        
        Plus penalty rules for structural/semantic deviations.
        """
        if weights is None:
            weights = {
                'cfg': 0.30,
                'dfg': 0.25,
                'instruction': 0.20,
                'memory': 0.15,
                'call_graph': 0.10,
            }

        # Imports are done locally to avoid circular dependencies
        from src.cfg_engine.cfg_builder import CFGBuilder
        from src.dfg_engine.dfg_builder import DFGBuilder
        from src.dfg_engine.memory_analyzer import MemoryBehaviorAnalyzer

        # 1. CFG Similarity (30%)
        cfg_builder = CFGBuilder()
        old_cfg = cfg_builder.build_from_function_ir(old_func.raw_text, old_func.name)
        new_cfg = cfg_builder.build_from_function_ir(new_func.raw_text, new_func.name)
        
        old_cfg_nodes = set(old_cfg.nodes.keys())
        new_cfg_nodes = set(new_cfg.nodes.keys())
        union_cfg_nodes = old_cfg_nodes | new_cfg_nodes
        cfg_node_sim = (len(old_cfg_nodes & new_cfg_nodes) / len(union_cfg_nodes) * 100) if union_cfg_nodes else 100.0
        
        old_cfg_edges = {(e.from_block, e.to_block) for e in old_cfg.edges}
        new_cfg_edges = {(e.from_block, e.to_block) for e in new_cfg.edges}
        union_cfg_edges = old_cfg_edges | new_cfg_edges
        cfg_edge_sim = (len(old_cfg_edges & new_cfg_edges) / len(union_cfg_edges) * 100) if union_cfg_edges else 100.0
        
        cfg_sim = 0.7 * cfg_node_sim + 0.3 * cfg_edge_sim

        # 2. DFG Similarity (25%)
        dfg_builder = DFGBuilder()
        old_dfg = dfg_builder.build_from_function_ir(old_func.raw_text, old_func.name)
        new_dfg = dfg_builder.build_from_function_ir(new_func.raw_text, new_func.name)
        
        old_dfg_nodes = {n.text for n in old_dfg.nodes.values()}
        new_dfg_nodes = {n.text for n in new_dfg.nodes.values()}
        union_dfg_nodes = old_dfg_nodes | new_dfg_nodes
        dfg_node_sim = (len(old_dfg_nodes & new_dfg_nodes) / len(union_dfg_nodes) * 100) if union_dfg_nodes else 100.0
        
        old_dfg_edges = {(e.source, e.target, e.edge_type) for e in old_dfg.edges}
        new_dfg_edges = {(e.source, e.target, e.edge_type) for e in new_dfg.edges}
        union_dfg_edges = old_dfg_edges | new_dfg_edges
        dfg_edge_sim = (len(old_dfg_edges & new_dfg_edges) / len(union_dfg_edges) * 100) if union_dfg_edges else 100.0
        
        dfg_sim = 0.7 * dfg_node_sim + 0.3 * dfg_edge_sim

        # 3. Instruction Similarity (20%)
        instr_sim = SimilarityScorer.function_similarity(old_func.instructions, new_func.instructions)

        # 4. Memory Behavior Similarity (15%)
        mem_analyzer = MemoryBehaviorAnalyzer()
        old_mem = mem_analyzer.analyze(old_func.raw_text)
        new_mem = mem_analyzer.analyze(new_func.raw_text)
        
        load_diff = abs(old_mem.load_count - new_mem.load_count)
        store_diff = abs(old_mem.store_count - new_mem.store_count)
        alloc_diff = abs(old_mem.memory_instruction_count - new_mem.memory_instruction_count)
        mem_sim = 100.0 - min(100.0, (load_diff + store_diff + alloc_diff) * 10.0)

        # 5. Function Call Graph Similarity (10%)
        call_sim = SimilarityScorer.call_graph_similarity(old_func.function_calls, new_func.function_calls)

        # Compute weighted composite score
        composite = (
            cfg_sim * weights['cfg']
            + dfg_sim * weights['dfg']
            + instr_sim * weights['instruction']
            + mem_sim * weights['memory']
            + call_sim * weights['call_graph']
        )

        # Penalty system
        penalties = 0.0

        # Added branch penalty (strong penalty)
        old_br_count = len(re.findall(r'\bbr\s+i1\b', old_func.raw_text))
        new_br_count = len(re.findall(r'\bbr\s+i1\b', new_func.raw_text))
        if new_br_count > old_br_count:
            penalties += 20.0 * (new_br_count - old_br_count)

        # Loop penalty (strong penalty)
        old_loops = len(old_cfg.loops)
        new_loops = len(new_cfg.loops)
        if new_loops > old_loops:
            penalties += 25.0 * (new_loops - old_loops)

        # Arithmetic operator change (medium penalty)
        old_ops = re.findall(r'\b(add|sub|mul|sdiv|udiv|shl|ashr|lshr|fadd|fsub|fmul|fdiv)\b', old_func.raw_text)
        new_ops = re.findall(r'\b(add|sub|mul|sdiv|udiv|shl|ashr|lshr|fadd|fsub|fmul|fdiv)\b', new_func.raw_text)
        if set(old_ops) != set(new_ops) and len(old_ops) > 0:
            penalties += 10.0

        # Apply penalties
        composite = max(0.0, composite - penalties)

        # Ensure that if it has ANY change, it's not reported as 100%
        if composite >= 99.5 and (old_func.raw_text != new_func.raw_text):
            composite = 99.0

        return min(100.0, max(0.0, composite))

    @staticmethod
    def instruction_diff(old_instructions: list, new_instructions: list) -> Tuple[list, list, list]:
        """
        Compare instruction lists and return (added, removed, modified).
        
        Returns:
            (added_instructions, removed_instructions, modified_pairs)
        """
        old_set = set(old_instructions)
        new_set = set(new_instructions)

        added = list(new_set - old_set)
        removed = list(old_set - new_set)

        # Find modified (similar but not identical)
        modified = []
        for old_instr in removed[:]:
            for new_instr in added[:]:
                sim = SimilarityScorer.instruction_similarity(old_instr, new_instr)
                if sim > 0.6:  # Threshold for "modified"
                    modified.append((old_instr, new_instr, sim))
                    removed.remove(old_instr)
                    added.remove(new_instr)
                    break

        return added, removed, modified

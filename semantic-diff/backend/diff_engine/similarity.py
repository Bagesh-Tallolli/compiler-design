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
        old_instructions: list,
        new_instructions: list,
        old_blocks: list,
        new_blocks: list,
        old_calls: list,
        new_calls: list,
        weights: dict = None,
    ) -> float:
        """Compute weighted composite similarity score (0-100)."""
        if weights is None:
            weights = {
                'instruction': 0.6,
                'block': 0.25,
                'call_graph': 0.15,
            }

        instr_sim = SimilarityScorer.function_similarity(old_instructions, new_instructions)
        block_sim = SimilarityScorer.block_similarity(old_blocks, new_blocks)
        call_sim = SimilarityScorer.call_graph_similarity(old_calls, new_calls)

        composite = (
            instr_sim * weights['instruction']
            + block_sim * weights['block']
            + call_sim * weights['call_graph']
        )

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

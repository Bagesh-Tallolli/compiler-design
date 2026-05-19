from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple
from .function_mapper import Function, FunctionMapper
from .similarity import SimilarityScorer


@dataclass
class FunctionDiff:
    """Represents the diff for a single function."""
    name: str
    status: str  # 'unchanged', 'changed', 'added', 'removed'
    similarity_score: float = 100.0
    old_function: Function = None
    new_function: Function = None
    added_instructions: List[str] = field(default_factory=list)
    removed_instructions: List[str] = field(default_factory=list)
    modified_instructions: List[Tuple[str, str, float]] = field(default_factory=list)
    added_blocks: List[str] = field(default_factory=list)
    removed_blocks: List[str] = field(default_factory=list)
    added_calls: List[str] = field(default_factory=list)
    removed_calls: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "similarity_score": round(self.similarity_score, 2),
            "instruction_changes": {
                "added": self.added_instructions,
                "removed": self.removed_instructions,
                "modified": [
                    {"from": old, "to": new, "similarity": round(sim, 2)}
                    for old, new, sim in self.modified_instructions
                ],
            },
            "block_changes": {
                "added": self.added_blocks,
                "removed": self.removed_blocks,
            },
            "call_changes": {
                "added": self.added_calls,
                "removed": self.removed_calls,
            },
            "change_count": len(self.added_instructions) + len(self.removed_instructions) + len(self.modified_instructions),
        }


@dataclass
class DiffSummary:
    """Overall diff summary between two IR files."""
    changed_functions: List[FunctionDiff] = field(default_factory=list)
    unchanged_functions: List[FunctionDiff] = field(default_factory=list)
    added_functions: List[FunctionDiff] = field(default_factory=list)
    removed_functions: List[FunctionDiff] = field(default_factory=list)

    def to_dict(self):
        total_score = 0.0
        match_count = 0
        for f in self.changed_functions + self.unchanged_functions:
            total_score += f.similarity_score
            match_count += 1
        avg_similarity = (total_score / match_count) if match_count > 0 else 100.0

        return {
            "changed": [f.to_dict() for f in self.changed_functions],
            "unchanged": [f.to_dict() for f in self.unchanged_functions],
            "added": [f.to_dict() for f in self.added_functions],
            "removed": [f.to_dict() for f in self.removed_functions],
            "summary": {
                "total_functions": self.total_functions(),
                "changed_count": len(self.changed_functions),
                "unchanged_count": len(self.unchanged_functions),
                "added_count": len(self.added_functions),
                "removed_count": len(self.removed_functions),
                "similarity_score": round(avg_similarity, 2),
            },
        }

    def total_functions(self):
        return (
            len(self.changed_functions)
            + len(self.unchanged_functions)
            + len(self.added_functions)
            + len(self.removed_functions)
        )


class IRDiffEngine:
    """Orchestrates semantic diffing of normalized LLVM IR."""

    def __init__(self):
        self.mapper = FunctionMapper()
        self.scorer = SimilarityScorer()

    def diff(self, old_ir: str, new_ir: str) -> DiffSummary:
        """Compare two normalized LLVM IR files.
        
        Returns DiffSummary with classified functions and differences.
        """
        # Extract functions
        old_functions = self.mapper.extract_functions(old_ir)
        new_functions = self.mapper.extract_functions(new_ir)

        summary = DiffSummary()

        old_names = set(old_functions.keys())
        new_names = set(new_functions.keys())

        # Process unchanged and changed functions
        for name in old_names & new_names:
            old_func = old_functions[name]
            new_func = new_functions[name]

            diff = self._diff_function(old_func, new_func)
            if diff.status == 'unchanged':
                summary.unchanged_functions.append(diff)
            else:
                summary.changed_functions.append(diff)

        # Process added functions
        for name in new_names - old_names:
            new_func = new_functions[name]
            diff = FunctionDiff(
                name=name,
                status='added',
                similarity_score=0.0,
                new_function=new_func,
            )
            summary.added_functions.append(diff)

        # Process removed functions
        for name in old_names - new_names:
            old_func = old_functions[name]
            diff = FunctionDiff(
                name=name,
                status='removed',
                similarity_score=0.0,
                old_function=old_func,
            )
            summary.removed_functions.append(diff)

        return summary

    def _diff_function(self, old_func: Function, new_func: Function) -> FunctionDiff:
        """Compare two function definitions."""
        # Calculate similarity
        similarity = self.scorer.composite_similarity(old_func, new_func)

        # Determine status (perfectly identical means unchanged, any change means changed)
        status = 'unchanged' if similarity >= 100.0 else 'changed'

        # Diff instructions
        added_instr, removed_instr, modified_instr = self.scorer.instruction_diff(
            old_func.instructions,
            new_func.instructions,
        )

        # Diff blocks
        old_block_labels = {block.label for block in old_func.blocks}
        new_block_labels = {block.label for block in new_func.blocks}
        added_blocks = list(new_block_labels - old_block_labels)
        removed_blocks = list(old_block_labels - new_block_labels)

        # Diff calls
        old_calls_set = set(old_func.function_calls)
        new_calls_set = set(new_func.function_calls)
        added_calls = list(new_calls_set - old_calls_set)
        removed_calls = list(old_calls_set - new_calls_set)

        diff = FunctionDiff(
            name=old_func.name,
            status=status,
            similarity_score=similarity,
            old_function=old_func,
            new_function=new_func,
            added_instructions=added_instr,
            removed_instructions=removed_instr,
            modified_instructions=modified_instr,
            added_blocks=added_blocks,
            removed_blocks=removed_blocks,
            added_calls=added_calls,
            removed_calls=removed_calls,
        )

        return diff

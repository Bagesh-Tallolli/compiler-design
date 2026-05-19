from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .cfg_builder import ControlFlowGraph
from .complexity import ComplexityAnalyzer


@dataclass
class CFGChange:
    """Represents a semantic change in CFG structure."""
    change_type: str  # 'added_branch', 'removed_branch', 'loop_structure_changed', 'block_split', 'block_merge', 'execution_path_changed'
    description: str
    old_element: str = None
    new_element: str = None
    impact_level: str = 'low'  # 'low', 'medium', 'high'

    def to_dict(self):
        return {
            'type': self.change_type,
            'description': self.description,
            'old': self.old_element,
            'new': self.new_element,
            'impact': self.impact_level,
        }


@dataclass
class CFGDiff:
    """Represents the diff between two CFGs."""
    function_name: str
    old_cfg: ControlFlowGraph
    new_cfg: ControlFlowGraph
    changes: List[CFGChange] = field(default_factory=list)
    complexity_comparison: Dict = None

    def to_dict(self):
        return {
            'function_name': self.function_name,
            'changes': [c.to_dict() for c in self.changes],
            'change_count': len(self.changes),
            'complexity': self.complexity_comparison,
            'old_graph': self.old_cfg.to_dict(),
            'new_graph': self.new_cfg.to_dict(),
        }


class CFGDiffEngine:
    """Compares two CFGs and detects semantic control-flow changes."""

    def diff(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> CFGDiff:
        """Compare two CFGs and return differences."""
        cfg_diff = CFGDiff(
            function_name=old_cfg.function_name,
            old_cfg=old_cfg,
            new_cfg=new_cfg,
        )

        # Detect changes
        changes = []

        # 1. Compare basic blocks
        changes.extend(self._detect_block_changes(old_cfg, new_cfg))

        # 2. Compare edges (branches)
        changes.extend(self._detect_edge_changes(old_cfg, new_cfg))

        # 3. Compare loop structures
        changes.extend(self._detect_loop_changes(old_cfg, new_cfg))

        # 4. Compare execution paths
        changes.extend(self._detect_path_changes(old_cfg, new_cfg))

        cfg_diff.changes = changes
        cfg_diff.complexity_comparison = ComplexityAnalyzer.complexity_comparison(old_cfg, new_cfg)

        return cfg_diff

    def _detect_block_changes(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> List[CFGChange]:
        """Detect added/removed blocks and block merges/splits."""
        changes = []

        old_labels = set(old_cfg.nodes.keys())
        new_labels = set(new_cfg.nodes.keys())

        # Added blocks
        added = new_labels - old_labels
        for block in added:
            changes.append(CFGChange(
                change_type='block_added',
                description=f'New basic block added: {block}',
                new_element=block,
                impact_level='medium',
            ))

        # Removed blocks
        removed = old_labels - new_labels
        for block in removed:
            changes.append(CFGChange(
                change_type='block_removed',
                description=f'Basic block removed: {block}',
                old_element=block,
                impact_level='medium',
            ))

        # Block merges: block with 1 successor that has 1 predecessor (in new, not in old)
        merges = self._detect_block_merges(old_cfg, new_cfg)
        for old_seq, merged_label in merges:
            changes.append(CFGChange(
                change_type='block_merge',
                description=f'Basic blocks merged: {old_seq} → {merged_label}',
                old_element=old_seq,
                new_element=merged_label,
                impact_level='low',
            ))

        # Block splits: one block in old becomes multiple in new
        splits = self._detect_block_splits(old_cfg, new_cfg)
        for old_label, new_seq in splits:
            changes.append(CFGChange(
                change_type='block_split',
                description=f'Basic block split: {old_label} → {new_seq}',
                old_element=old_label,
                new_element=new_seq,
                impact_level='medium',
            ))

        return changes

    def _detect_edge_changes(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> List[CFGChange]:
        """Detect added/removed branches."""
        changes = []

        old_edges = {(e.from_block, e.to_block): e for e in old_cfg.edges}
        new_edges = {(e.from_block, e.to_block): e for e in new_cfg.edges}

        old_keys = set(old_edges.keys())
        new_keys = set(new_edges.keys())

        # Added edges
        added = new_keys - old_keys
        for (from_block, to_block) in added:
            edge = new_edges[(from_block, to_block)]
            description = f'Branch added: {from_block} → {to_block}'
            if edge.branch_type == 'conditional':
                description += f' (condition: {edge.condition})'
            changes.append(CFGChange(
                change_type='branch_added',
                description=description,
                new_element=f'{from_block}->{to_block}',
                impact_level='high',
            ))

        # Removed edges
        removed = old_keys - new_keys
        for (from_block, to_block) in removed:
            edge = old_edges[(from_block, to_block)]
            description = f'Branch removed: {from_block} → {to_block}'
            if edge.branch_type == 'conditional':
                description += f' (condition: {edge.condition})'
            changes.append(CFGChange(
                change_type='branch_removed',
                description=description,
                old_element=f'{from_block}->{to_block}',
                impact_level='high',
            ))

        return changes

    def _detect_loop_changes(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> List[CFGChange]:
        """Detect changes in loop structures."""
        changes = []

        old_loops = set(old_cfg.loops)
        new_loops = set(new_cfg.loops)

        # New loops
        new_loop_headers = new_loops - old_loops
        for header in new_loop_headers:
            changes.append(CFGChange(
                change_type='loop_added',
                description=f'New loop detected with header: {header}',
                new_element=header,
                impact_level='high',
            ))

        # Removed loops
        removed_loop_headers = old_loops - new_loops
        for header in removed_loop_headers:
            changes.append(CFGChange(
                change_type='loop_removed',
                description=f'Loop removed (header was: {header})',
                old_element=header,
                impact_level='high',
            ))

        return changes

    def _detect_path_changes(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> List[CFGChange]:
        """Detect changes in execution paths."""
        changes = []

        # Compare entry-to-exit paths
        old_paths = self._compute_execution_paths(old_cfg)
        new_paths = self._compute_execution_paths(new_cfg)

        if old_paths != new_paths:
            changes.append(CFGChange(
                change_type='execution_path_changed',
                description=f'Execution path structure changed ({len(old_paths)} → {len(new_paths)} paths)',
                impact_level='high',
            ))

        return changes

    def _detect_block_merges(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> List[Tuple[str, str]]:
        """Detect when blocks are merged."""
        merges = []
        # Simplified: compare predecessor/successor patterns
        return merges

    def _detect_block_splits(self, old_cfg: ControlFlowGraph, new_cfg: ControlFlowGraph) -> List[Tuple[str, str]]:
        """Detect when blocks are split."""
        splits = []
        # Simplified: compare instruction count patterns
        return splits

    def _compute_execution_paths(self, cfg: ControlFlowGraph) -> int:
        """Compute number of distinct execution paths (approximation)."""
        if not cfg.entry_block:
            return 0

        path_count = [0]
        path_stack = set()

        def dfs(node_label):
            if node_label in path_stack:
                return
            path_stack.add(node_label)

            if node_label in cfg.exit_blocks:
                path_count[0] += 1
            elif node_label in cfg.nodes:
                node = cfg.nodes[node_label]
                if len(node.successors) == 0:
                    path_count[0] += 1
                else:
                    for succ in node.successors:
                        dfs(succ)
            
            path_stack.remove(node_label)

        dfs(cfg.entry_block)
        return max(1, path_count[0])

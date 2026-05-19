import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class BasicBlockNode:
    """Represents a basic block in the CFG."""
    label: str
    instructions: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    is_loop_header: bool = False

    def to_dict(self):
        return {
            'label': self.label,
            'instruction_count': len(self.instructions),
            'successor_count': len(self.successors),
            'is_entry': self.is_entry,
            'is_exit': self.is_exit,
            'is_loop_header': self.is_loop_header,
        }


@dataclass
class Edge:
    """Represents an edge between two basic blocks."""
    from_block: str
    to_block: str
    branch_type: str = 'unconditional'  # 'conditional' or 'unconditional'
    condition: str = None  # e.g., 'true_branch', 'false_branch'
    is_back_edge: bool = False  # Indicates loop back edge

    def to_dict(self):
        return {
            'from': self.from_block,
            'to': self.to_block,
            'type': self.branch_type,
            'condition': self.condition,
            'is_back_edge': self.is_back_edge,
        }


class ControlFlowGraph:
    """Represents the control flow graph of a function."""

    def __init__(self, function_name: str):
        self.function_name = function_name
        self.nodes: Dict[str, BasicBlockNode] = {}
        self.edges: List[Edge] = []
        self.entry_block = None
        self.exit_blocks = []
        self.loops = []  # List of loop header labels

    def add_node(self, label: str, instructions: List[str], is_exit: bool = False):
        """Add a basic block node."""
        node = BasicBlockNode(label=label, instructions=instructions, is_exit=is_exit)
        self.nodes[label] = node

    def add_edge(self, from_label: str, to_label: str, branch_type: str = 'unconditional', condition: str = None):
        """Add an edge between blocks."""
        edge = Edge(from_block=from_label, to_block=to_label, branch_type=branch_type, condition=condition)
        self.edges.append(edge)

        # Update successor/predecessor lists
        if from_label in self.nodes:
            if to_label not in self.nodes[from_label].successors:
                self.nodes[from_label].successors.append(to_label)
        if to_label in self.nodes:
            if from_label not in self.nodes[to_label].predecessors:
                self.nodes[to_label].predecessors.append(from_label)

    def mark_entry(self, label: str):
        """Mark a block as entry."""
        if label in self.nodes:
            self.nodes[label].is_entry = True
            self.entry_block = label

    def mark_exit(self, label: str):
        """Mark a block as exit."""
        if label in self.nodes:
            self.nodes[label].is_exit = True
            self.exit_blocks.append(label)

    def detect_loops(self):
        """Detect loops by identifying back edges."""
        # Simple algorithm: find nodes with predecessors that are descendants (back edges)
        visited = set()
        rec_stack = set()
        back_edges = []

        def dfs(node_label):
            visited.add(node_label)
            rec_stack.add(node_label)

            if node_label in self.nodes:
                for succ in self.nodes[node_label].successors:
                    if succ not in visited:
                        dfs(succ)
                    elif succ in rec_stack:
                        back_edges.append((node_label, succ))
                        # Mark successor as loop header
                        if succ in self.nodes:
                            self.nodes[succ].is_loop_header = True
                            self.loops.append(succ)

            rec_stack.remove(node_label)

        if self.entry_block:
            dfs(self.entry_block)

        # Mark back edges
        for from_label, to_label in back_edges:
            for edge in self.edges:
                if edge.from_block == from_label and edge.to_block == to_label:
                    edge.is_back_edge = True

    def to_dict(self):
        """Serialize CFG to dictionary."""
        return {
            'function_name': self.function_name,
            'nodes': {label: node.to_dict() for label, node in self.nodes.items()},
            'edges': [edge.to_dict() for edge in self.edges],
            'entry_block': self.entry_block,
            'exit_blocks': self.exit_blocks,
            'loops': self.loops,
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
        }


class CFGBuilder:
    """Builds CFG from normalized LLVM IR."""

    def __init__(self):
        pass

    def build_from_function_ir(self, func_ir: str, function_name: str) -> ControlFlowGraph:
        """Build CFG from a function's normalized LLVM IR."""
        cfg = ControlFlowGraph(function_name)

        lines = func_ir.split('\n')
        blocks = self._extract_blocks(lines)

        if not blocks:
            return cfg

        # Add nodes
        first_block = True
        for block_label, instructions in blocks.items():
            is_exit = self._is_exit_block(instructions)
            cfg.add_node(block_label, instructions, is_exit=is_exit)
            if first_block:
                cfg.mark_entry(block_label)
                first_block = False

        # Extract branches and add edges
        for block_label, instructions in blocks.items():
            self._add_edges_from_block(cfg, block_label, instructions)

        # Detect loops
        cfg.detect_loops()

        return cfg

    def _extract_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        """Extract basic blocks from IR lines."""
        blocks = {}
        current_block = None
        current_instructions = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('{') or stripped.startswith('}'):
                continue

            # Block label (ends with :)
            if stripped.endswith(':') and not stripped.startswith('!'):
                if current_block:
                    blocks[current_block] = current_instructions
                current_block = stripped[:-1]
                current_instructions = []
            elif not stripped.startswith('!'):
                if current_block is None:
                    current_block = "entry"
                current_instructions.append(stripped)

        if current_block:
            blocks[current_block] = current_instructions

        return blocks

    def _add_edges_from_block(self, cfg: ControlFlowGraph, block_label: str, instructions: List[str]):
        """Extract branch instructions and add edges."""
        for instr in instructions:
            if 'br i1' in instr:  # Conditional branch
                # Pattern: br i1 %cond, label %block1, label %block2
                match = re.search(r'br i1 .+?, label %(\w+), label %(\w+)', instr)
                if match:
                    true_block = match.group(1)
                    false_block = match.group(2)
                    cfg.add_edge(block_label, true_block, branch_type='conditional', condition='true')
                    cfg.add_edge(block_label, false_block, branch_type='conditional', condition='false')
            elif 'br label' in instr:  # Unconditional branch
                # Pattern: br label %block
                match = re.search(r'br label %(\w+)', instr)
                if match:
                    target_block = match.group(1)
                    cfg.add_edge(block_label, target_block, branch_type='unconditional')
            elif 'switch' in instr:  # Switch statement
                # Pattern: switch <type> %var, label %default [ <cases> ]
                matches = re.findall(r'label %(\w+)', instr)
                for target in matches:
                    cfg.add_edge(block_label, target, branch_type='conditional')

    def _is_exit_block(self, instructions: List[str]) -> bool:
        """Check if block is an exit block (contains return)."""
        return any('ret' in instr for instr in instructions)

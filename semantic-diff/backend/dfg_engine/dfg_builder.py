import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


ARITHMETIC_OPS = {"add", "sub", "mul", "sdiv", "udiv", "srem", "urem"}
MEMORY_OPS = {"load", "store", "alloca", "memcpy", "memmove"}
LOGIC_OPS = {"and", "or", "xor", "icmp", "fcmp"}
FUNCTION_OPS = {"call", "invoke"}
ALL_TRACKED_OPS = ARITHMETIC_OPS | MEMORY_OPS | LOGIC_OPS | FUNCTION_OPS


@dataclass
class DFGNode:
    name: str
    opcode: str
    text: str
    defines: List[str] = field(default_factory=list)
    uses: List[str] = field(default_factory=list)
    block: Optional[str] = None
    kind: str = "compute"

    def to_dict(self):
        return {
            "name": self.name,
            "opcode": self.opcode,
            "text": self.text,
            "defines": self.defines,
            "uses": self.uses,
            "block": self.block,
            "kind": self.kind,
        }


@dataclass
class DFGEdge:
    source: str
    target: str
    edge_type: str = "data"

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
        }


@dataclass
class DataFlowGraph:
    function_name: str
    nodes: Dict[str, DFGNode] = field(default_factory=dict)
    edges: List[DFGEdge] = field(default_factory=list)
    memory_nodes: List[str] = field(default_factory=list)
    call_nodes: List[str] = field(default_factory=list)
    load_nodes: List[str] = field(default_factory=list)
    store_nodes: List[str] = field(default_factory=list)
    producers: Dict[str, List[str]] = field(default_factory=dict)
    consumers: Dict[str, List[str]] = field(default_factory=dict)

    def add_node(self, node: DFGNode):
        self.nodes[node.name] = node
        if node.kind == "memory":
            self.memory_nodes.append(node.name)
        if node.kind == "call":
            self.call_nodes.append(node.name)
        if node.opcode == "load":
            self.load_nodes.append(node.name)
        if node.opcode == "store":
            self.store_nodes.append(node.name)

    def add_edge(self, source: str, target: str, edge_type: str = "data"):
        if source == target:
            return
        self.edges.append(DFGEdge(source=source, target=target, edge_type=edge_type))
        self.producers.setdefault(target, []).append(source)
        self.consumers.setdefault(source, []).append(target)

    @property
    def node_count(self):
        return len(self.nodes)

    @property
    def edge_count(self):
        return len(self.edges)

    def to_dict(self):
        return {
            "function_name": self.function_name,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "memory_nodes": self.memory_nodes,
            "call_nodes": self.call_nodes,
            "load_nodes": self.load_nodes,
            "store_nodes": self.store_nodes,
            "producers": self.producers,
            "consumers": self.consumers,
        }


class DFGBuilder:
    """Build reusable data flow graphs from normalized LLVM IR."""

    def build_from_function_ir(self, func_ir: str, function_name: str) -> DataFlowGraph:
        graph = DataFlowGraph(function_name=function_name)
        instructions = self._extract_instructions(func_ir)
        definition_map: Dict[str, str] = {}

        for index, instr in enumerate(instructions):
            opcode = self._extract_opcode(instr)
            if not opcode:
                continue

            if opcode not in ALL_TRACKED_OPS:
                continue

            node_name = f"{function_name}_n{index}"
            defines = self._extract_defines(instr)
            uses = self._extract_uses(instr)
            kind = self._classify_kind(opcode)
            node = DFGNode(
                name=node_name,
                opcode=opcode,
                text=instr,
                defines=defines,
                uses=uses,
                kind=kind,
            )
            graph.add_node(node)

            for defined in defines:
                definition_map[defined] = node_name

            for use in uses:
                producer = definition_map.get(use)
                if producer:
                    graph.add_edge(producer, node_name, edge_type=self._edge_type_for_opcode(opcode))

        self._link_memory_chains(graph)
        self._link_call_dependencies(graph)
        return graph

    def _extract_instructions(self, func_ir: str) -> List[str]:
        lines = []
        for raw_line in func_ir.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("define ") or line == "{" or line == "}":
                continue
            if line.endswith(":"):
                continue
            lines.append(line)
        return lines

    def _extract_opcode(self, instr: str) -> Optional[str]:
        match = re.match(r"(?:%[\w\.]+\s*=\s*)?(\w+)", instr)
        return match.group(1) if match else None

    def _extract_defines(self, instr: str) -> List[str]:
        match = re.match(r"^(%[\w\.]+)\s*=", instr)
        return [match.group(1)] if match else []

    def _extract_uses(self, instr: str) -> List[str]:
        uses = re.findall(r"%[\w\.]+", instr)
        if uses and self._extract_defines(instr):
            defined = self._extract_defines(instr)[0]
            uses = [item for item in uses if item != defined]
        return uses

    def _classify_kind(self, opcode: str) -> str:
        if opcode in MEMORY_OPS:
            return "memory"
        if opcode in FUNCTION_OPS:
            return "call"
        if opcode in ARITHMETIC_OPS:
            return "arithmetic"
        if opcode in LOGIC_OPS:
            return "logic"
        return "compute"

    def _edge_type_for_opcode(self, opcode: str) -> str:
        if opcode in MEMORY_OPS:
            return "memory"
        if opcode in FUNCTION_OPS:
            return "call"
        if opcode in ARITHMETIC_OPS:
            return "arithmetic"
        if opcode in LOGIC_OPS:
            return "logic"
        return "data"

    def _link_memory_chains(self, graph: DataFlowGraph):
        last_memory_node = None
        for node in graph.nodes.values():
            if node.opcode in MEMORY_OPS:
                if last_memory_node:
                    graph.add_edge(last_memory_node, node.name, edge_type="memory_chain")
                last_memory_node = node.name

    def _link_call_dependencies(self, graph: DataFlowGraph):
        last_call_node = None
        for node in graph.nodes.values():
            if node.opcode in FUNCTION_OPS:
                if last_call_node:
                    graph.add_edge(last_call_node, node.name, edge_type="call_chain")
                last_call_node = node.name

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .dfg_builder import DataFlowGraph
from .memory_analyzer import MemoryBehaviorAnalyzer


@dataclass
class DFGChange:
    change_type: str
    description: str
    impact: str = "low"
    old_element: str = None
    new_element: str = None

    def to_dict(self):
        return {
            "type": self.change_type,
            "description": self.description,
            "impact": self.impact,
            "old": self.old_element,
            "new": self.new_element,
        }


@dataclass
class DFGDiff:
    function_name: str
    dfg_changes: List[DFGChange] = field(default_factory=list)
    memory_changes: Dict = field(default_factory=dict)
    dependency_changes: List[Dict] = field(default_factory=list)
    similarity: Dict = field(default_factory=dict)
    old_graph: DataFlowGraph = None
    new_graph: DataFlowGraph = None

    def to_dict(self):
        return {
            "function_name": self.function_name,
            "dfg_changes": [change.to_dict() for change in self.dfg_changes],
            "memory_changes": self.memory_changes,
            "dependency_changes": self.dependency_changes,
            "similarity": self.similarity,
            "old_graph": self.old_graph.to_dict() if self.old_graph else None,
            "new_graph": self.new_graph.to_dict() if self.new_graph else None,
            "change_count": len(self.dfg_changes) + len(self.dependency_changes),
        }


class DFGDiffEngine:
    """Compares two DFGs and reports data-flow semantic changes."""

    def __init__(self):
        self.memory_analyzer = MemoryBehaviorAnalyzer()

    def diff(self, old_graph: DataFlowGraph, new_graph: DataFlowGraph, old_func_ir: str = "", new_func_ir: str = "") -> DFGDiff:
        old_nodes = {node.text for node in old_graph.nodes.values()}
        new_nodes = {node.text for node in new_graph.nodes.values()}
        old_edges = {(edge.source, edge.target, edge.edge_type) for edge in old_graph.edges}
        new_edges = {(edge.source, edge.target, edge.edge_type) for edge in new_graph.edges}

        changes: List[DFGChange] = []
        dependency_changes: List[Dict] = []

        for instr in sorted(new_nodes - old_nodes):
            changes.append(DFGChange("added_computation", f"Added computation: {instr}", "medium", new_element=instr))
        for instr in sorted(old_nodes - new_nodes):
            changes.append(DFGChange("removed_computation", f"Removed computation: {instr}", "medium", old_element=instr))

        added_edges = new_edges - old_edges
        removed_edges = old_edges - new_edges
        if added_edges or removed_edges:
            dependency_changes.append({
                "description": "Dependency chain expanded" if added_edges else "Dependency chain reduced",
                "added_edges": [f"{s}->{t}:{k}" for s, t, k in sorted(added_edges)],
                "removed_edges": [f"{s}->{t}:{k}" for s, t, k in sorted(removed_edges)],
                "impact": "high" if len(added_edges) > len(removed_edges) else "medium",
            })

        if self._arithmetic_changed(old_graph, new_graph):
            changes.append(DFGChange("arithmetic_behavior_changed", "Arithmetic behavior modified", "high"))

        if len(new_nodes) > len(old_nodes):
            changes.append(DFGChange("dataflow_expanded", "Dependency chain expanded", "medium"))
        elif len(new_nodes) < len(old_nodes):
            changes.append(DFGChange("dataflow_reduced", "Dependency chain reduced", "medium"))

        memory_changes = self._memory_changes(old_func_ir, new_func_ir)
        similarity = self._similarity(old_graph, new_graph)

        return DFGDiff(
            function_name=old_graph.function_name,
            dfg_changes=changes,
            memory_changes=memory_changes,
            dependency_changes=dependency_changes,
            similarity=similarity,
            old_graph=old_graph,
            new_graph=new_graph,
        )

    def _arithmetic_changed(self, old_graph: DataFlowGraph, new_graph: DataFlowGraph) -> bool:
        old_arith = [n.text for n in old_graph.nodes.values() if n.kind == "arithmetic"]
        new_arith = [n.text for n in new_graph.nodes.values() if n.kind == "arithmetic"]
        return old_arith != new_arith

    def _memory_changes(self, old_ir: str, new_ir: str) -> Dict:
        if not old_ir or not new_ir:
            return {"old": {}, "new": {}, "delta": {}, "impact": "unknown"}
        old_behavior = self.memory_analyzer.analyze(old_ir)
        new_behavior = self.memory_analyzer.analyze(new_ir)
        comparison = self.memory_analyzer.compare(old_behavior, new_behavior)
        if comparison["delta"]["load_count"] > 0 or comparison["delta"]["store_count"] > 0:
            comparison["semantic_label"] = "Memory access increased"
        elif comparison["delta"]["load_count"] < 0 or comparison["delta"]["store_count"] < 0:
            comparison["semantic_label"] = "Memory access reduced"
        else:
            comparison["semantic_label"] = "Memory behavior unchanged"
        return comparison

    def _similarity(self, old_graph: DataFlowGraph, new_graph: DataFlowGraph) -> Dict:
        old_nodes = {node.text for node in old_graph.nodes.values()}
        new_nodes = {node.text for node in new_graph.nodes.values()}
        old_edges = {(e.source, e.target, e.edge_type) for e in old_graph.edges}
        new_edges = {(e.source, e.target, e.edge_type) for e in new_graph.edges}
        node_overlap = len(old_nodes & new_nodes) / max(1, len(old_nodes | new_nodes))
        edge_overlap = len(old_edges & new_edges) / max(1, len(old_edges | new_edges))
        score = round((node_overlap * 0.7 + edge_overlap * 0.3) * 100, 2)
        return {
            "score": score,
            "node_similarity": round(node_overlap * 100, 2),
            "edge_similarity": round(edge_overlap * 100, 2),
        }

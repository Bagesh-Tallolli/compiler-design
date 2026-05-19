import re
from dataclasses import dataclass
from typing import Dict


@dataclass
class MemoryBehavior:
    load_count: int = 0
    store_count: int = 0
    memory_instruction_count: int = 0
    pointer_usage_count: int = 0
    alias_sensitive_ops: int = 0

    def to_dict(self):
        return {
            "load_count": self.load_count,
            "store_count": self.store_count,
            "memory_instruction_count": self.memory_instruction_count,
            "pointer_usage_count": self.pointer_usage_count,
            "alias_sensitive_ops": self.alias_sensitive_ops,
        }


class MemoryBehaviorAnalyzer:
    """Analyzes memory behavior from normalized LLVM IR."""

    def analyze(self, func_ir: str) -> MemoryBehavior:
        behavior = MemoryBehavior()
        for line in func_ir.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            if re.search(r"\bload\b", stripped):
                behavior.load_count += 1
                behavior.memory_instruction_count += 1
            if re.search(r"\bstore\b", stripped):
                behavior.store_count += 1
                behavior.memory_instruction_count += 1
            if re.search(r"\balloca\b|\bmemcpy\b|\bmemmove\b", stripped):
                behavior.memory_instruction_count += 1
            if "*" in stripped or re.search(r"ptr\b", stripped):
                behavior.pointer_usage_count += 1
            if re.search(r"\bgetelementptr\b|\bbitcast\b", stripped):
                behavior.alias_sensitive_ops += 1
        return behavior

    def compare(self, old_behavior: MemoryBehavior, new_behavior: MemoryBehavior) -> Dict:
        delta = {
            "load_count": new_behavior.load_count - old_behavior.load_count,
            "store_count": new_behavior.store_count - old_behavior.store_count,
            "memory_instruction_count": new_behavior.memory_instruction_count - old_behavior.memory_instruction_count,
            "pointer_usage_count": new_behavior.pointer_usage_count - old_behavior.pointer_usage_count,
            "alias_sensitive_ops": new_behavior.alias_sensitive_ops - old_behavior.alias_sensitive_ops,
        }
        impact = self._impact(delta)
        return {
            "old": old_behavior.to_dict(),
            "new": new_behavior.to_dict(),
            "delta": delta,
            "impact": impact,
        }

    def _impact(self, delta: Dict) -> str:
        score = delta["load_count"] + delta["store_count"] + delta["memory_instruction_count"]
        if score >= 4:
            return "high_increase"
        if score >= 1:
            return "moderate_increase"
        if score <= -4:
            return "high_decrease"
        if score < 0:
            return "decrease"
        return "unchanged"

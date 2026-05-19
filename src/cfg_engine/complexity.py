from typing import Dict


class ComplexityAnalyzer:
    """Computes cyclomatic complexity and related metrics."""

    @staticmethod
    def cyclomatic_complexity(node_count: int, edge_count: int, connected_components: int = 1, cfg=None) -> int:
        """
        Compute cyclomatic complexity.
        If cfg is provided, use decision counting for maximum accuracy.
        Otherwise, fall back to E - N + 2P.
        
        Where:
        - E = edges
        - N = nodes
        - P = connected components (typically 1)
        
        Returns: complexity value
        """
        if cfg is not None:
            import re
            decision_points = 0
            for node in cfg.nodes.values():
                for instr in node.instructions:
                    # 1. Conditional branch
                    if 'br i1' in instr:
                        decision_points += 1
                    # 2. Switch statement
                    elif 'switch ' in instr:
                        labels = re.findall(r'label\s+%\w+', instr)
                        if len(labels) > 1:
                            decision_points += (len(labels) - 1)
            return 1 + decision_points

        if node_count == 0:
            return 1
        return edge_count - node_count + 2 * connected_components

    @staticmethod
    def loop_complexity_bonus(loop_count: int) -> int:
        """Additional complexity for each loop detected."""
        return loop_count

    @staticmethod
    def total_complexity(cfg) -> int:
        """Compute total complexity including loops."""
        cyclo = ComplexityAnalyzer.cyclomatic_complexity(
            len(cfg.nodes),
            len(cfg.edges),
            cfg=cfg
        )
        loop_bonus = ComplexityAnalyzer.loop_complexity_bonus(len(cfg.loops))
        return cyclo + loop_bonus

    @staticmethod
    def complexity_comparison(old_cfg, new_cfg) -> Dict:
        """Compare complexity metrics between two CFGs."""
        old_cyclo = ComplexityAnalyzer.cyclomatic_complexity(
            len(old_cfg.nodes),
            len(old_cfg.edges),
            cfg=old_cfg
        )
        new_cyclo = ComplexityAnalyzer.cyclomatic_complexity(
            len(new_cfg.nodes),
            len(new_cfg.edges),
            cfg=new_cfg
        )

        old_total = ComplexityAnalyzer.total_complexity(old_cfg)
        new_total = ComplexityAnalyzer.total_complexity(new_cfg)

        old_loops = len(old_cfg.loops)
        new_loops = len(new_cfg.loops)

        return {
            'old': {
                'cyclomatic': old_cyclo,
                'loop_count': old_loops,
                'total_complexity': old_total,
                'node_count': len(old_cfg.nodes),
                'edge_count': len(old_cfg.edges),
            },
            'new': {
                'cyclomatic': new_cyclo,
                'loop_count': new_loops,
                'total_complexity': new_total,
                'node_count': len(new_cfg.nodes),
                'edge_count': len(new_cfg.edges),
            },
            'delta': {
                'cyclomatic_change': new_cyclo - old_cyclo,
                'loop_change': new_loops - old_loops,
                'total_complexity_change': new_total - old_total,
                'node_change': len(new_cfg.nodes) - len(old_cfg.nodes),
                'edge_change': len(new_cfg.edges) - len(old_cfg.edges),
            },
            'impact': ComplexityAnalyzer._classify_impact(new_total - old_total),
        }

    @staticmethod
    def _classify_impact(complexity_delta: int) -> str:
        """Classify complexity impact."""
        if complexity_delta > 0:
            if complexity_delta >= 3:
                return 'high_increase'
            elif complexity_delta >= 1:
                return 'moderate_increase'
            return 'slight_increase'
        elif complexity_delta < 0:
            return 'decreased'
        else:
            return 'unchanged'

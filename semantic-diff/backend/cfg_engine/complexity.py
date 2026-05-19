from typing import Dict


class ComplexityAnalyzer:
    """Computes cyclomatic complexity and related metrics."""

    @staticmethod
    def cyclomatic_complexity(node_count: int, edge_count: int, connected_components: int = 1) -> int:
        """
        Compute cyclomatic complexity using: M = E - N + 2P
        
        Where:
        - E = edges
        - N = nodes
        - P = connected components (typically 1)
        
        Returns: complexity value
        """
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
            cfg.node_count,
            cfg.edge_count,
        )
        loop_bonus = ComplexityAnalyzer.loop_complexity_bonus(len(cfg.loops))
        return cyclo + loop_bonus

    @staticmethod
    def complexity_comparison(old_cfg, new_cfg) -> Dict:
        """Compare complexity metrics between two CFGs."""
        old_cyclo = ComplexityAnalyzer.cyclomatic_complexity(
            old_cfg.node_count,
            old_cfg.edge_count,
        )
        new_cyclo = ComplexityAnalyzer.cyclomatic_complexity(
            new_cfg.node_count,
            new_cfg.edge_count,
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
                'node_count': old_cfg.node_count,
                'edge_count': old_cfg.edge_count,
            },
            'new': {
                'cyclomatic': new_cyclo,
                'loop_count': new_loops,
                'total_complexity': new_total,
                'node_count': new_cfg.node_count,
                'edge_count': new_cfg.edge_count,
            },
            'delta': {
                'cyclomatic_change': new_cyclo - old_cyclo,
                'loop_change': new_loops - old_loops,
                'total_complexity_change': new_total - old_total,
                'node_change': new_cfg.node_count - old_cfg.node_count,
                'edge_change': new_cfg.edge_count - old_cfg.edge_count,
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

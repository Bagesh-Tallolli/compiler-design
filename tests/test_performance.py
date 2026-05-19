import unittest
from pathlib import Path
from src.performance_engine.performance_analyzer import PerformanceIntelligenceEngine
from src.cfg_engine.cfg_builder import CFGBuilder
from src.dfg_engine.dfg_builder import DFGBuilder

class TestPerformanceIntelligence(unittest.TestCase):
    """Verifies that the Performance Intelligence Engine produces accurate performance scores and analytics."""

    def setUp(self):
        self.engine = PerformanceIntelligenceEngine()
        self.cfg_builder = CFGBuilder()
        self.dfg_builder = DFGBuilder()

    def test_o1_complexity(self):
        ir = """
        define i32 @test(i32 %x) {
        entry:
          %v = add nsw i32 %x, 5
          ret i32 %v
        }
        """
        cfg = self.cfg_builder.build_from_function_ir(ir, "test")
        complexity, loop_count = self.engine._estimate_complexity(cfg, ir)
        self.assertEqual(complexity, "O(1)")
        self.assertEqual(loop_count, 0)

    def test_on_complexity(self):
        # A simple simulated loop with a single loop backedge
        ir = """
        define i32 @test(i32 %x) {
        entry:
          br label %loop_cond
        loop_cond:
          %i = phi i32 [ 0, %entry ], [ %i_next, %loop_body ]
          %cmp = icmp slt i32 %i, %x
          br i1 %cmp, label %loop_body, label %loop_exit
        loop_body:
          %i_next = add nsw i32 %i, 1
          br label %loop_cond
        loop_exit:
          ret i32 0
        }
        """
        cfg = self.cfg_builder.build_from_function_ir(ir, "test")
        complexity, loop_count = self.engine._estimate_complexity(cfg, ir)
        self.assertEqual(complexity, "O(n)")
        self.assertEqual(loop_count, 1)

    def test_memory_impact_array(self):
        old_ir = "define i32 @test() {\n  %x = alloca i32\n  ret i32 0\n}"
        new_ir = "define i32 @test() {\n  %arr = alloca [100 x i32]\n  ret i32 0\n}"
        
        impact, explanation = self.engine._estimate_memory_impact(old_ir, new_ir, None, None)
        self.assertEqual(impact, "Increased Memory")
        self.assertIn("array", explanation)

if __name__ == '__main__':
    unittest.main()

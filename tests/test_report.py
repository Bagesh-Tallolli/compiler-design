import unittest
from src.report_engine.report_generator import ReportGenerator
from src.diff_engine.function_mapper import Function

class TestReportGenerator(unittest.TestCase):
    """Verifies that the Human-Friendly Semantic Intelligence Engine produces accurate risk scores and layouts."""

    def setUp(self):
        self.report_gen = ReportGenerator()

    def test_api_change_detection(self):
        # Create simulated Function objects with different signatures
        old_func = Function(
            name="process",
            return_type="i32",
            arguments=["i32 %x"]
        )
        new_func = Function(
            name="process",
            return_type="double",
            arguments=["double %x"]
        )

        res = self.report_gen.classify_function_change(
            func_name="process",
            similarity=80.0,
            cfg_diff={},
            dfg_diff={},
            gained_opts=[],
            lost_opts=[],
            old_func_obj=old_func,
            new_func_obj=new_func
        )
        self.assertEqual(res["classification"], "API Change")
        self.assertEqual(res["risk_level"], "HIGH")
        self.assertIn("parameter types or return signature", res["what_changed"])

    def test_critical_security_auth_bypass(self):
        # Simulation of an authentication check being bypassed to return constant true
        old_cpp = """
        bool login(string password) {
            if (password == "12345") {
                return true;
            }
            return false;
        }
        """
        new_cpp = """
        bool login(string password) {
            return true;
        }
        """
        res = self.report_gen.classify_function_change(
            func_name="login",
            similarity=70.0,
            cfg_diff={},
            dfg_diff={},
            gained_opts=[],
            lost_opts=[],
            old_cpp_src=old_cpp,
            new_cpp_src=new_cpp
        )
        self.assertEqual(res["classification"], "Security-Relevant Change")
        self.assertEqual(res["risk_level"], "CRITICAL")
        self.assertIn("CRITICAL security risk", res["risk_explanation"])

    def test_high_security_null_check_removal(self):
        old_cpp = """
        void process(int* ptr) {
            if (ptr == nullptr) return;
            *ptr = 10;
        }
        """
        new_cpp = """
        void process(int* ptr) {
            *ptr = 10;
        }
        """
        res = self.report_gen.classify_function_change(
            func_name="process",
            similarity=90.0,
            cfg_diff={},
            dfg_diff={},
            gained_opts=[],
            lost_opts=[],
            old_cpp_src=old_cpp,
            new_cpp_src=new_cpp
        )
        self.assertEqual(res["classification"], "Security-Relevant Change")
        self.assertEqual(res["risk_level"], "HIGH")
        self.assertIn("Null pointer check", res["risk_explanation"])

    def test_12_sections_layout(self):
        func_classifications = [{
            "name": "dummy",
            "similarity": 95.0,
            "classification": "Structural Refactor",
            "risk_level": "LOW",
            "risk_explanation": "Minor refactoring",
            "performance_impact": "Neutral",
            "gained_optimizations": [],
            "lost_optimizations": [],
            "security_findings": [],
            "logic_mutation": "",
            "execution_example": "",
            "complexity_shift": "",
            "memory_shift": "",
            "old_complexity": "O(1) [Constant Time]",
            "new_complexity": "O(1) [Constant Time]",
            "old_cpp_func": "",
            "new_cpp_func": "",
            "what_changed": "Reorganized blocks.",
            "why_it_matters": "No behavior impact."
        }]

        report = self.report_gen.generate_report(
            old_file_name="old.cpp",
            new_file_name="new.cpp",
            summary_dict={"summary": {"similarity_score": 95.0}},
            function_classifications=func_classifications,
            cfg_analyses=[],
            dfg_analyses=[]
        )

        # Assert exactly 12 sections are present by checking their titles
        expected_sections = [
            "1. EXECUTIVE SUMMARY",
            "2. WHAT CHANGED",
            "3. BEHAVIOR DIFFERENCE",
            "4. SPEED IMPACT",
            "5. MEMORY USAGE IMPACT",
            "6. COMPILER OPTIMIZATION IMPACT",
            "7. SECURITY IMPACT",
            "8. RISK LEVEL",
            "9. SIMILARITY SCORE",
            "10. TECHNICAL LLVM DETAILS",
            "11. PLAIN ENGLISH SUMMARY",
            "12. FINAL RECOMMENDATION"
        ]
        for section in expected_sections:
            self.assertIn(section, report)

if __name__ == '__main__':
    unittest.main()

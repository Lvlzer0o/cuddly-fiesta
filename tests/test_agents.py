import unittest
import os
import tempfile

from cuddly_fiesta import agents


class TestAgents(unittest.TestCase):
    def test_run_all_smoke(self):
        """run_all executes without raising an exception"""
        agents.run_all()

    def test_health_check(self):
        """health_check returns a boolean"""
        result = agents.health_check()
        self.assertIsInstance(result, bool)

    def test_generate_report(self):
        """generate_report creates a file and returns its path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.txt")
            out_path = agents.generate_report(path)
            self.assertTrue(os.path.exists(out_path))


if __name__ == "__main__":
    unittest.main()

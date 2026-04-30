import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VakSelfCheckExampleTests(unittest.TestCase):
    def test_vak_self_check_example_passes(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "vak.py", "examples/vak_self_check.vak"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Vak आत्म-परीक्षा पूर्ण", result.stdout)
        self.assertIn("कुल विफलताएँ: 0", result.stdout)
        self.assertIn("✓ कोडेक्स उन्नयन रिपोर्ट", result.stdout)
        self.assertIn("✓ सान्समैटिक अनुक्रम पाठ", result.stdout)
        self.assertIn("✓ colour_lib compatibility lookup", result.stdout)
        self.assertIn("✓ चित्रकला कैनवास चौड़ाई", result.stdout)
        self.assertIn("✓ प्रदर्शन चरण उपलब्ध", result.stdout)


if __name__ == "__main__":
    unittest.main()

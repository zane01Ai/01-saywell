import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "evals/random-run/build-blind.py"
spec = importlib.util.spec_from_file_location("build_blind", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BuildBlindTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a, self.b = self.root / "a.md", self.root / "b.md"
        self.a.write_text("## 【S01】\n第一份甲文\n## 【S02】\n第二份甲文\n", encoding="utf-8")
        self.b.write_text("## 【S01】\n第一份乙文\n## 【S02】\n第二份乙文\n", encoding="utf-8")

    def test_deterministic_complete_pairs(self):
        first = module.build(self.a, self.b, 7)
        self.assertEqual(first, module.build(self.a, self.b, 7))
        body, answers = first
        self.assertEqual(set(answers), {"01", "02"})
        for record in answers.values():
            self.assertEqual(set(record.values()), {"A", "B"})
        for text in ["第一份甲文", "第二份甲文", "第一份乙文", "第二份乙文"]:
            self.assertEqual(body.count(text), 1)

    def test_unpaired_ids_rejected(self):
        self.b.write_text("## 【S01】\n只有一份\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unpaired IDs"):
            module.build(self.a, self.b, 7)

    def test_duplicate_ids_rejected(self):
        self.a.write_text("## 【S01】\n第一份\n## 【S1】\n重复编号\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            module.build(self.a, self.b, 7)

    def test_cli_independent_of_cwd_and_no_overwrite(self):
        out = self.root / "out"
        command = [sys.executable, str(SCRIPT), "--a", str(self.a), "--b", str(self.b), "--out-dir", str(out)]
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads((out / "answer-key.json").read_text(encoding="utf-8"))), 2)
        old = (out / "blind-package.md").read_bytes()
        again = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual((out / "blind-package.md").read_bytes(), old)


if __name__ == "__main__":
    unittest.main()

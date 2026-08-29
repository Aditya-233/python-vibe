import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finetune.huggingface_store import write_card
from finetune.models import HF_USER, SPECS


class HuggingFaceStoreTest(unittest.TestCase):
    def test_repo_lives_under_yauhenbichel(self) -> None:
        self.assertEqual(HF_USER, "YauhenBichel")
        self.assertEqual(SPECS["python-vibe"].hf_repo, "YauhenBichel/python-vibe-0.5b")
        self.assertEqual(list(SPECS), ["python-vibe"])

    def test_write_card(self) -> None:
        spec = SPECS["python-vibe"]
        with tempfile.TemporaryDirectory() as tmp:
            readme = write_card(spec, Path(tmp))
            text = readme.read_text(encoding="utf-8")
        self.assertIn("python-vibe-0.5b", text)
        self.assertIn("YauhenBichel/python-vibe-0.5b", text)


if __name__ == "__main__":
    unittest.main()

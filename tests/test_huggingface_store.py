import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finetune.huggingface_store import stage_adapter_bundle, write_card
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
        self.assertIn("hf download YauhenBichel/python-vibe-0.5b", text)
        self.assertIn("github.com/YauhenBichel/python-vibe", text)

    def test_stage_adapter_bundle_drops_local_paths(self) -> None:
        spec = SPECS["python-vibe"]
        if not (spec.adapter_path / "adapter_config.json").is_file():
            self.skipTest("local adapters not on this machine")
        dest = stage_adapter_bundle(spec)
        cfg = json.loads((dest / "adapter_config.json").read_text(encoding="utf-8"))
        dumped = json.dumps(cfg)
        self.assertNotIn("/Users/", dumped)
        self.assertIn("lora_parameters", cfg)
        self.assertTrue((dest / "adapters.safetensors").is_file())
        self.assertTrue((dest / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()

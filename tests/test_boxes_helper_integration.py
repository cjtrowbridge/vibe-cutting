import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", MODULE_PATH)
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)


class BoxesHelperIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = helper_tool.get_tool("boxes")
        if not helper_tool.inspect_tool(cls.tool)["ready"]:
            raise unittest.SkipTest("Boxes.py helper environment is not installed.")

    def generate(self, root):
        config = root / "generator.yml"
        output = root / "generated"
        output.mkdir()
        config.write_text(
            "Defaults:\n"
            "  reference: 0\n"
            "Boxes:\n"
            "  - box_type: RegularBox\n"
            "    name: smoke\n"
            "    args:\n"
            "      thickness: 3\n"
            "      burn: 0.1\n",
            encoding="utf-8",
        )
        result = helper_tool.run_tool(
            self.tool,
            ["--multi-generator", str(config), str(output)],
        )
        self.assertEqual(result, 0)
        artifact = output / "smoke_0.svg"
        self.assertTrue(artifact.is_file())
        return artifact.read_bytes()

    def test_reproducible_svg_generation(self):
        temporary_root = REPO_ROOT / ".tmp"
        with tempfile.TemporaryDirectory(dir=temporary_root) as first_directory:
            with tempfile.TemporaryDirectory(dir=temporary_root) as second_directory:
                first = self.generate(Path(first_directory))
                second = self.generate(Path(second_directory))
        self.assertEqual(first, second)
        self.assertNotIn(b"<dc:date>", first)
        self.assertNotIn(b"Creation date:", first)
        ET.fromstring(first)
        self.assertTrue(helper_tool.source_is_clean(self.tool))


if __name__ == "__main__":
    unittest.main()

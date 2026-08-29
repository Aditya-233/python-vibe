"""Drop-in editor files and MCP handshake. No model."""

import json
import tempfile
import unittest
from pathlib import Path

from harness.editor_kit import install_editors
from harness.mcp_stdio import handle_rpc
from harness.model.openai_compat import chat_completion_payload, last_user_text
from harness.skillkit.catalog import list_skills, pick_skills
from harness.locate import prelude, refuse_redundant_locate
from harness.scan.project_brief import start_hint
from harness.scan.project_brief import classify_project
from harness.task import (
    everyday_skill_name,
    looks_like_algorithm,
    looks_like_analytics,
    looks_like_http_client,
    looks_like_script,
)


class EverydayKindsTest(unittest.TestCase):
    def test_script_http_analytics_algorithm(self) -> None:
        self.assertTrue(looks_like_script("write a weekday script from argv"))
        self.assertTrue(looks_like_http_client("fetch json from the HTTP API"))
        self.assertTrue(looks_like_http_client("call the api like curl would"))
        self.assertTrue(looks_like_analytics("tally counts by key from a csv"))
        self.assertTrue(looks_like_algorithm("implement binary search"))
        self.assertFalse(looks_like_script("what does weekday_name return?"))
        self.assertEqual(everyday_skill_name("implement binary search"), "write-algorithm")
        self.assertEqual(everyday_skill_name("fetch json from the HTTP API"), "call-http")

    def test_pick_loads_the_narrow_skill(self) -> None:
        catalog = list_skills()

        def names(task: str) -> list[str]:
            return [item.name for item in pick_skills(task, catalog)]

        self.assertEqual(
            names("write a weekday script from argv"),
            ["write-script", "write-tests"],
        )
        self.assertEqual(
            names("fetch json from the HTTP API"),
            ["call-http", "write-tests"],
        )
        self.assertEqual(
            names("tally counts by key from a csv"),
            ["analyze-data", "write-tests"],
        )
        self.assertEqual(
            names("implement binary search"),
            ["write-algorithm", "write-tests"],
        )

    def test_prelude_and_hint_ask_for_edit_not_patch(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            (root / "pkg").mkdir()
            (root / "pkg" / "app.py").write_text("def go() -> int:\n    return 1\n")
            text, _path = prelude(root, "implement binary search")
            hint = start_hint(classify_project(root), "fetch json from the HTTP API")
        self.assertIn("edit Path: pkg/index_of.py", text)
        self.assertIn("write-algorithm", text)
        self.assertNotIn("Append:", text)
        self.assertIn("call-http", hint)
        self.assertIn("edit Path: pkg/fetch_json.py", hint)
        self.assertIn(
            "edit Path: pkg/index_of.py",
            refuse_redundant_locate("implement binary search", "locate", True),
        )


class ChatHelpersTest(unittest.TestCase):
    def test_last_user_text_from_parts(self) -> None:
        messages = [
            {"role": "system", "content": "you are a helper"},
            {
                "role": "user",
                "content": [{"type": "text", "text": "what does add return?"}],
            },
        ]
        self.assertEqual(last_user_text(messages), "what does add return?")

    def test_completion_shape(self) -> None:
        payload = chat_completion_payload("int", "llama3.1:8b")
        self.assertEqual(payload["object"], "chat.completion")
        self.assertEqual(payload["choices"][0]["message"]["content"], "int")


ROOT = Path(__file__).resolve().parents[1]


class EditorInstallTest(unittest.TestCase):
    def test_vscode_and_continue_and_cursor(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            vscode = install_editors(root, "vscode")
            cont = install_editors(root, "continue")
            cursor = install_editors(root, "cursor")
            self.assertTrue(vscode[0].is_file())
            self.assertIn("python-vibe: ask", vscode[0].read_text(encoding="utf-8"))
            self.assertIn("127.0.0.1:8081", cont[0].read_text(encoding="utf-8"))
            mcp = json.loads(cursor[0].read_text(encoding="utf-8"))
            self.assertIn("mcp", mcp["mcpServers"]["python-vibe"]["args"])
            self.assertIn(root.resolve().as_posix(), json.dumps(mcp))
            self.assertEqual(
                mcp["mcpServers"]["python-vibe"]["command"],
                Path(__import__("sys").executable).as_posix(),
            )

    def test_unknown_kind_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                install_editors(Path(tmp), "notepad")


class McpHandshakeTest(unittest.TestCase):
    def test_initialize_and_list_need_no_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init = handle_rpc(
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                project=project,
                allow_writes=False,
                model="none",
            )
            listed = handle_rpc(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                project=project,
                allow_writes=False,
                model="none",
            )
        assert init is not None and listed is not None
        self.assertEqual(init["result"]["serverInfo"]["name"], "python-vibe")
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertEqual(names, {"ask", "run"})

    def test_run_is_refused_when_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            reply = handle_rpc(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "run",
                        "arguments": {"task": "add multiply(a, b)"},
                    },
                },
                project=Path(tmp),
                allow_writes=False,
                model="none",
            )
        assert reply is not None
        self.assertTrue(reply["result"]["isError"])
        self.assertIn("read-only", reply["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()

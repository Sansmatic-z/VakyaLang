import io
import json
import unittest

from runtime.tooling.lsp_server import VakLanguageServer, VakLanguageTools


class VakToolingTests(unittest.TestCase):
    def setUp(self):
        self.tools = VakLanguageTools()

    def test_analyze_document_reports_compile_errors(self):
        diagnostics = self.tools.analyze_document("यदि सत्य मुद्रय १\n", filename="broken.vak")
        self.assertTrue(diagnostics)
        self.assertIn("broken.vak", diagnostics[0].message)

    def test_completion_includes_keywords_and_builtins(self):
        items = self.tools.completion_items("मु", 0, 2)
        labels = {item["label"] for item in items}
        self.assertIn("मुद्रय", labels)

    def test_hover_returns_keyword_documentation(self):
        hover = self.tools.hover("मुद्रय १\n", 0, 1)
        self.assertIsNotNone(hover)
        self.assertIn("Builtin print/output function", hover["contents"]["value"])

    def test_document_symbols_and_definition_resolve_top_level_names(self):
        source = (
            "स्थिर नाम = \"vak\"\n"
            "कर्म दोगुना(x):\n"
            "    प्रत्यागच्छ x * २\n"
            "वर्ग गणक:\n"
            "    कर्म __init__(स्वयं):\n"
            "        स्वयं.मान = ०\n"
        )
        symbols = self.tools.document_symbols(source)
        names = {item["name"] for item in symbols}
        self.assertIn("नाम", names)
        self.assertIn("दोगुना", names)
        self.assertIn("गणक", names)

        definition = self.tools.definition(source + "मुद्रय दोगुना(३)\n", 6, 8)
        self.assertTrue(definition)
        self.assertEqual(definition[0]["range"]["start"]["line"], 1)


class VakLanguageServerTests(unittest.TestCase):
    def test_server_processes_initialize_and_completion(self):
        server = VakLanguageServer(in_stream=io.BytesIO(), out_stream=io.BytesIO())
        response, notifications = server.process_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        self.assertFalse(notifications)
        self.assertTrue(response["result"]["capabilities"]["hoverProvider"])

        _, notifications = server.process_request(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": "file:///memory.vak",
                        "text": "मुद्रय १\n",
                    }
                },
            }
        )
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]["method"], "textDocument/publishDiagnostics")

        response, notifications = server.process_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/completion",
                "params": {
                    "textDocument": {"uri": "file:///memory.vak"},
                    "position": {"line": 0, "character": 2},
                },
            }
        )
        self.assertFalse(notifications)
        labels = {item["label"] for item in response["result"]["items"]}
        self.assertIn("मुद्रय", labels)

    def test_server_writes_valid_lsp_frames(self):
        out_stream = io.BytesIO()
        server = VakLanguageServer(in_stream=io.BytesIO(), out_stream=out_stream)
        server._write_message({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})
        payload = out_stream.getvalue()
        self.assertIn(b"Content-Length:", payload)
        self.assertIn(b"\r\n\r\n", payload)
        body = payload.split(b"\r\n\r\n", 1)[1]
        self.assertEqual(json.loads(body.decode("utf-8"))["result"]["ok"], True)


if __name__ == "__main__":
    unittest.main()

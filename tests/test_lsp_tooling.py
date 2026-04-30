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

    def test_analyze_document_reports_multiple_parse_errors_after_recovery(self):
        diagnostics = self.tools.analyze_document(
            "मान x =\nस्थिर y =\n",
            filename="broken_many.vak",
        )
        self.assertGreaterEqual(len(diagnostics), 2)
        self.assertTrue(all("broken_many.vak" in item.message for item in diagnostics[:2]))

    def test_analyze_document_emits_rupantar_hint_for_repairable_source(self):
        diagnostics = self.tools.analyze_document("चर सूची = []\nसूची.apend(१)\n", filename="broken.vak")
        self.assertTrue(any(item.source == "vak-rupantar" for item in diagnostics))

    def test_completion_includes_keywords_and_builtins(self):
        items = self.tools.completion_items("मु", 0, 2)
        labels = {item["label"] for item in items}
        self.assertIn("मुद्रय", labels)

    def test_completion_includes_document_symbols_and_modules(self):
        source = "कर्म दोगुना(x):\n    प्रत्यागच्छ x * २\nदो"
        items = self.tools.completion_items(source, 2, 2)
        labels = {item["label"] for item in items}
        self.assertIn("दोगुना", labels)

    def test_hover_returns_keyword_documentation(self):
        hover = self.tools.hover("मुद्रय १\n", 0, 1)
        self.assertIsNotNone(hover)
        self.assertIn("Vak output printer", hover["contents"]["value"])

    def test_hover_returns_function_signature_with_type_information(self):
        source = (
            "कर्म दोगुना(x: संख्या) → संख्या:\n"
            "    प्रत्यागच्छ x * २\n"
            "मुद्रय दोगुना(३)\n"
        )
        hover = self.tools.hover(source, 2, 8)
        self.assertIsNotNone(hover)
        self.assertIn("कर्म दोगुना(x: संख्या) → संख्या", hover["contents"]["value"])

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

    def test_code_actions_offer_rupantar_and_codex_rewrites(self):
        repair_actions = self.tools.code_actions(
            "चर सूची = []\nसूची.apend(१)\n",
            filename="broken.vak",
            uri="file:///broken.vak",
        )
        self.assertTrue(any("वाक्य-रूपान्तर" in item["title"] for item in repair_actions))

        codex_actions = self.tools.code_actions(
            "karma yoga(x, y):\n    pratyagaccha x + y\n",
            filename="sample.svk",
            uri="file:///sample.svk",
        )
        self.assertTrue(any(item["title"].startswith("कोडेक्स") for item in codex_actions))

    def test_signature_help_resolves_user_defined_functions(self):
        source = (
            "कर्म दोगुना(x: संख्या, y=२) → संख्या:\n"
            "    प्रत्यागच्छ x * y\n"
            "मुद्रय दोगुना(३, "
        )
        signature = self.tools.signature_help(source, 2, len("मुद्रय दोगुना(३, "))
        self.assertIsNotNone(signature)
        self.assertIn("कर्म दोगुना(x: संख्या, y = ...) → संख्या", signature["signatures"][0]["label"])
        self.assertEqual(signature["activeParameter"], 1)


class VakLanguageServerTests(unittest.TestCase):
    def test_server_processes_initialize_and_completion(self):
        server = VakLanguageServer(in_stream=io.BytesIO(), out_stream=io.BytesIO())
        response, notifications = server.process_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        self.assertFalse(notifications)
        self.assertTrue(response["result"]["capabilities"]["hoverProvider"])
        self.assertTrue(response["result"]["capabilities"]["codeActionProvider"])
        self.assertIn("signatureHelpProvider", response["result"]["capabilities"])

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

    def test_server_processes_code_actions_and_windows_file_uris(self):
        server = VakLanguageServer(in_stream=io.BytesIO(), out_stream=io.BytesIO())
        uri = "file:///C:/Temp/%E0%A4%A8%E0%A4%AE%E0%A5%82%E0%A4%A8%E0%A4%BE.vak"
        _, notifications = server.process_request(
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": uri,
                        "text": "चर सूची = []\nसूची.apend(१)\n",
                    }
                },
            }
        )
        self.assertEqual(notifications[0]["params"]["uri"], uri)
        self.assertTrue(server._path_from_uri(uri).endswith("नमूना.vak"))

        response, notifications = server.process_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "textDocument/codeAction",
                "params": {
                    "textDocument": {"uri": uri},
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 12},
                    },
                    "context": {"diagnostics": []},
                },
            }
        )
        self.assertFalse(notifications)
        self.assertTrue(any("वाक्य-रूपान्तर" in item["title"] for item in response["result"]))

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

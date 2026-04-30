import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from runtime.src.tui import VakTuiApp, main as tui_main


class VakTuiEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.cwd = Path(self.tempdir.name)
        self.app = VakTuiApp(cwd=self.cwd, use_rich=False, clear_screen=False)

    def test_repl_and_sandbox_manager_preserve_state_per_sandbox(self):
        self.app.set_mode("repl")
        self.app.execute_command("चर संख्या = ७")
        output = self.app.execute_command("मुद्रय संख्या")
        self.assertIn("7", output)

        self.app.set_mode("sandbox")
        self.app.execute_command("new प्रयोग")
        globals_output = self.app.execute_command("globals प्रयोग")
        self.assertNotIn("संख्या", globals_output)

        self.app.execute_command("switch default")
        self.app.set_mode("repl")
        again = self.app.execute_command("मुद्रय संख्या")
        self.assertIn("7", again)

        self.app.set_mode("sandbox")
        self.app.execute_command("reset default")
        reset_output = self.app.execute_command("globals default")
        self.assertNotIn("संख्या", reset_output)

    def test_sansmatic_explorer_updates_live_state(self):
        self.app.set_mode("proof")
        self.app.execute_command("define अग्नि ताप")
        self.app.execute_command("assert अग्नि HAS ताप")
        self.app.execute_command("rule अग्नि HAS ताप => अग्नि IS तेज")
        result = self.app.execute_command("eval अग्नि IS तेज")
        self.assertIn("सिद्ध", result)
        backward = self.app.execute_command("backward अग्नि IS तेज")
        self.assertIn("लक्ष्य सिद्ध", backward)
        snapshot = self.app.execute_command("snapshot तेज_स्थिति")
        self.assertIn("तेज_स्थिति", snapshot)
        self.app.execute_command("reset")
        restored = self.app.execute_command("restore तेज_स्थिति")
        self.assertIn("तेज_स्थिति", restored)
        trace = self.app.execute_command("trace 5")
        self.assertIn("rule_fire", trace)
        tree = self.app.execute_command("tree अग्नि IS तेज")
        self.assertIn("proved_by_rule", tree)
        rendered = self.app.render_text()
        self.assertIn("तथ्य: 1", rendered)
        self.assertIn("व्युत्पन्न: 1", rendered)
        self.assertIn("अग्नि HAS ताप", rendered)
        self.assertIn("अग्नि IS तेज", rendered)

    def test_sansmatic_explorer_supports_theorem_commands(self):
        self.app.set_mode("proof")
        self.app.execute_command("define अग्नि ताप")
        registered = self.app.execute_command("theorem fact ताप_प्रमेय अग्नि HAS ताप")
        self.assertIn("प्रमेय पंजीकृत", registered)
        listed = self.app.execute_command("theorem list")
        self.assertIn("ताप_प्रमेय", listed)
        shown = self.app.execute_command("theorem show ताप_प्रमेय")
        self.assertIn("प्रमेय: ताप_प्रमेय", shown)
        self.assertIn("वचन: अग्नि HAS ताप", shown)

    def test_chitrakala_studio_creates_preview_and_saves_png(self):
        if not self.app.chitra_support.available:
            self.skipTest("Chitrakala support unavailable in this environment")

        self.app.set_mode("chitra")
        self.app.execute_command("new 32 24 white")
        self.app.execute_command("line 0 0 31 23 black")
        self.app.execute_command("mandala 16 12 8 6")
        target = self.cwd / "tui_demo.png"
        result = self.app.execute_command(f"save {target.name}")
        self.assertIn("चित्र सहेजा गया", result)
        self.assertTrue(target.exists())
        rendered = self.app.render_text()
        self.assertIn("32x24", rendered)

    def test_vpm_panel_initializes_project(self):
        self.app.set_mode("vpm")
        result = self.app.execute_command("init")
        self.assertIn("vakya.json", result)
        self.assertTrue((self.cwd / "vakya.json").exists())
        self.app.execute_command("installed")
        rendered = self.app.render_text()
        self.assertIn("स्थापित पैकेज", rendered)

    def test_vpm_panel_supports_lock_cache_and_python_dependency_removal(self):
        self.app.set_mode("vpm")
        self.app.execute_command("init")
        self.app.vpm._save_python_dep("requests>=2")
        python_rows = self.app.execute_command("python")
        self.assertIn("Python निर्भरताएँ: 1", python_rows)
        lock_result = self.app.execute_command("lock")
        self.assertIn("लॉकफ़ाइल", lock_result)
        self.assertTrue((self.cwd / "vakya.lock.json").exists())
        cache_result = self.app.execute_command("cache")
        self.assertIn("कैश जानकारी", cache_result)
        removed = self.app.execute_command("remove-py requests")
        self.assertIn("Python dependency", removed)
        rendered = self.app.render_text()
        self.assertIn("लॉकफ़ाइल: हाँ", rendered)

    def test_repair_workspace_loads_runs_diff_and_applies(self):
        source_path = self.cwd / "broken.vak"
        source_path.write_text(
            "चर सूची = []\nसूची.apend(१)\nमुद्रर सूची\n",
            encoding="utf-8",
        )
        self.app.set_mode("repair")
        self.app.execute_command(f"load {source_path.name}")
        report = self.app.execute_command("analyze")
        self.assertIn("वाक्य-रूपान्तर रिपोर्ट", report)
        diff = self.app.execute_command("diff")
        self.assertIn("सूची.apend(१)", diff)
        self.assertIn("सूची.जोड़ो(१)", diff)
        applied = self.app.execute_command("apply")
        self.assertIn("रूपान्तर परिणाम लिखा गया", applied)
        self.assertIn("सूची.जोड़ो(१)", source_path.read_text(encoding="utf-8"))

    def test_repair_workspace_supports_workspace_reload_branch_save_and_reject(self):
        source_path = self.cwd / "repair_workspace.vak"
        source_path.write_text("चर सूची = []\nसूची.apend(१)\n", encoding="utf-8")
        self.app.set_mode("repair")
        self.app.execute_command(f"open {source_path.name}")
        workspace = self.app.execute_command("workspace")
        self.assertIn("कार्यस्थल: रूपान्तर", workspace)
        self.assertIn("विश्लेषण: नहीं", workspace)
        branches = self.app.execute_command("branch adaptive_rupantar on")
        self.assertIn("adaptive_rupantar", branches)
        self.app.execute_command("analyze")
        saved = self.app.execute_command("save")
        saved_path = self.cwd / "repair_workspace.rupantar.vak"
        self.assertIn(str(saved_path), saved)
        self.assertTrue(saved_path.exists())
        self.assertIn("सूची.जोड़ो(१)", saved_path.read_text(encoding="utf-8"))
        source_path.write_text("चर सूची = []\nसूची.append(१)\n", encoding="utf-8")
        reloaded = self.app.execute_command("reload")
        self.assertIn("पुनः लोड", reloaded)
        rejected = self.app.execute_command("reject")
        self.assertIn("हटाया गया", rejected)
        workspace_after = self.app.execute_command("workspace")
        self.assertIn("विश्लेषण: नहीं", workspace_after)

    def test_codex_workspace_loads_runs_diff_and_applies(self):
        source_path = self.cwd / "roman.svk"
        source_path.write_text(
            "karma yoga(x, y):\n    pratyagaccha x + y\n",
            encoding="utf-8",
        )
        self.app.set_mode("codex")
        chapters = self.app.execute_command("chapters")
        self.assertIn("vak_core", chapters)
        pages = self.app.execute_command("pages")
        self.assertIn("vak", pages)
        self.app.execute_command(f"load {source_path.name}")
        self.app.execute_command("page auto")
        report = self.app.execute_command("analyze")
        self.assertIn("संस्कृत-वाक्य यूनिवर्सल कोडेक्स रिपोर्ट", report)
        diff = self.app.execute_command("diff")
        self.assertIn("karma yoga(x, y):", diff)
        self.assertIn("कर्म yoga(x, y):", diff)
        applied = self.app.execute_command("apply")
        self.assertIn("कोडेक्स परिणाम लिखा गया", applied)
        self.assertIn("कर्म yoga(x, y):", source_path.read_text(encoding="utf-8"))
        rendered = self.app.render_text()
        self.assertIn("कोडेक्स", rendered)

    def test_codex_workspace_supports_workspace_reload_branch_save_and_promotion(self):
        source_path = self.cwd / "sample.c"
        source_path.write_text(
            "int main() {\n    int x = 1;\n    printf(\"%d\", x);\n    return 0;\n}\n",
            encoding="utf-8",
        )
        self.app.set_mode("codex")
        self.app.execute_command(f"open {source_path.name}")
        workspace = self.app.execute_command("workspace")
        self.assertIn("कार्यस्थल: कोडेक्स", workspace)
        self.assertIn("पृष्ठ: auto", workspace)
        branches = self.app.execute_command("branch universal_codex_lab on")
        self.assertIn("universal_codex_lab", branches)
        self.app.execute_command("page c_subset")
        report = self.app.execute_command("promotion c_subset")
        self.assertIn("कोडेक्स उन्नयन रिपोर्ट", report)
        self.assertIn("c_subset", report)
        self.app.execute_command("analyze")
        saved = self.app.execute_command("save")
        saved_path = self.cwd / "sample.codex.c"
        self.assertIn(str(saved_path), saved)
        self.assertTrue(saved_path.exists())
        self.assertIn("कर्म main():", saved_path.read_text(encoding="utf-8"))
        source_path.write_text("int main() {\n    return 0;\n}\n", encoding="utf-8")
        reloaded = self.app.execute_command("reload")
        self.assertIn("पुनः लोड", reloaded)
        rejected = self.app.execute_command("reject")
        self.assertIn("हटाया गया", rejected)

    def test_builtin_and_module_help_commands_are_available(self):
        builtins_output = self.app.execute_command("builtins proof")
        codex_builtins_output = self.app.execute_command("builtins codex")
        modules_output = self.app.execute_command("modules")
        self.assertIn("प्रमाण_सारांश", builtins_output)
        self.assertIn("कोडेक्स_विवरण", codex_builtins_output)
        self.assertIn("कोडेक्स_उन्नयन", codex_builtins_output)
        self.assertIn("रंग_पुस्तकालय", modules_output)

    def test_cli_main_supports_noninteractive_commands(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = tui_main(
                [
                    "--plain",
                    "--mode",
                    "repl",
                    "--cwd",
                    str(self.cwd),
                    "--no-clear",
                    "--command",
                    "चर संख्या = ७",
                    "--command",
                    "मुद्रय संख्या",
                ]
            )
        self.assertEqual(code, 0)
        output = buffer.getvalue()
        self.assertIn("REPL", output)
        self.assertIn("7", output)


if __name__ == "__main__":
    unittest.main()

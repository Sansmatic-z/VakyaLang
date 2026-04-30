import unittest

from runtime.src.runtime_catalog import build_builtin_catalog, builtin_alias_map
from runtime.src.stdlib_manifest import (
    build_stdlib_manifest,
    canonical_module_specs,
    compatibility_module_names,
    module_alias_map,
    resolve_module_name,
)
from runtime.src.vm import VakVM


class RuntimeCatalogTests(unittest.TestCase):
    def test_builtin_catalog_exposes_live_proof_and_repair_surfaces(self):
        vm = VakVM()
        catalog = build_builtin_catalog(vm.builtins)
        aliases = builtin_alias_map(vm.builtins)

        self.assertIn("प्रमाण_सारांश", catalog)
        self.assertIn("रूपान्तर", catalog)
        self.assertIn("कोडेक्स", catalog)
        self.assertIn("कोडेक्स_अध्याय", catalog)
        self.assertIn("कोडेक्स_उन्नयन", catalog)
        self.assertIn("प्रदर्शन_विवरण", catalog)
        self.assertIn("आयात_प्रदर्शन_विवरण", catalog)
        self.assertIn("अतुल्य_अग्रिम", catalog)
        self.assertIn("अतुल्य_समाप्त", catalog)
        self.assertIn("प्रमाण_सारांश_पाठ", catalog)
        self.assertIn("प्रमेय_सूची", catalog)
        self.assertEqual(aliases["print"], "मुद्रय")
        self.assertEqual(catalog["खोलो"].category, "io")
        self.assertEqual(catalog["कोडेक्स"].category, "codex")
        self.assertEqual(catalog["कोडेक्स_उन्नयन"].category, "codex")
        self.assertEqual(catalog["प्रदर्शन_विवरण"].category, "tooling")
        self.assertEqual(catalog["अतुल्य_अग्रिम"].category, "async")

    def test_stdlib_manifest_marks_colour_lib_as_compatibility(self):
        manifest = build_stdlib_manifest()
        aliases = module_alias_map()

        self.assertIn("colour_lib", manifest)
        self.assertEqual(manifest["colour_lib"].tier, "compatibility")
        self.assertEqual(manifest["colour_lib"].canonical, "रंग_पुस्तकालय")
        self.assertEqual(aliases["गणित"], "ganit")
        self.assertIn("colour_lib", compatibility_module_names())
        self.assertEqual(resolve_module_name("color_lib"), "रंग_पुस्तकालय")
        self.assertIn("रंग_पुस्तकालय", canonical_module_specs())


if __name__ == "__main__":
    unittest.main()

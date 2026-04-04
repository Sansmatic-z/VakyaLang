import unittest

from runtime.src.runtime_catalog import build_builtin_catalog, builtin_alias_map
from runtime.src.stdlib_manifest import build_stdlib_manifest, module_alias_map
from runtime.src.vm import VakVM


class RuntimeCatalogTests(unittest.TestCase):
    def test_builtin_catalog_exposes_live_proof_and_repair_surfaces(self):
        vm = VakVM()
        catalog = build_builtin_catalog(vm.builtins)
        aliases = builtin_alias_map(vm.builtins)

        self.assertIn("प्रमाण_सारांश", catalog)
        self.assertIn("रूपान्तर", catalog)
        self.assertEqual(aliases["print"], "मुद्रय")
        self.assertEqual(catalog["खोलो"].category, "io")

    def test_stdlib_manifest_marks_colour_lib_as_compatibility(self):
        manifest = build_stdlib_manifest()
        aliases = module_alias_map()

        self.assertIn("colour_lib", manifest)
        self.assertEqual(manifest["colour_lib"].tier, "compatibility")
        self.assertEqual(manifest["colour_lib"].canonical, "रंग_पुस्तकालय")
        self.assertEqual(aliases["गणित"], "ganit")


if __name__ == "__main__":
    unittest.main()

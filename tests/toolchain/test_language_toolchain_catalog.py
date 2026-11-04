import unittest

from tools.toolchain.validate_language_catalog import load_catalog, validate


class LanguageToolchainCatalogTests(unittest.TestCase):
    def test_catalog_contract(self):
        validate(load_catalog())

    def test_expected_language_families(self):
        names = {entry["name"] for entry in load_catalog()["languages"]}
        self.assertTrue({"C", "C++", "Rust", "Python", "JavaScript",
                         "TypeScript", "C#", "Fortran", "COBOL",
                         "Assembly", "V", "Odin", "Raku", "GNU Octave",
                         "Verilog", "SystemVerilog", "VHDL"}.issubset(names))

    def test_both_os_products_share_the_catalog_contract(self):
        systems = load_catalog()["operating_systems"]
        self.assertEqual(set(systems), {"ChimeraIIOS", "OctavianOS"})
        for system in systems.values():
            self.assertEqual(system["shared_capability_contract"], "CHM-LANGUAGE-TOOLCHAIN-1")
            self.assertIn("hardware-description", system["optional_provider_profiles"])

    def test_no_false_native_installation_claims(self):
        for entry in load_catalog()["languages"]:
            self.assertFalse(entry["native_abi_claim"])
            self.assertEqual(entry["capability_status"],
                             "available-when-provider-installed")


if __name__ == "__main__":
    unittest.main()

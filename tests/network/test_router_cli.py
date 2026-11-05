import importlib.util
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("chimera_router_cli", ROOT / "tools/network/chimera_router_cli.py")
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

class RouterCliTests(unittest.TestCase):
    def test_ios_show_route(self):
        with patch.object(mod.platform, "system", return_value="Linux"):
            p = mod.translate("ios", "show ip route")
        self.assertEqual(p.argv, [["ip", "-4", "route", "show"]])
        self.assertFalse(p.mutating)
    def test_ios_static_route(self):
        with patch.object(mod.platform, "system", return_value="Linux"):
            p = mod.translate("ios", "ip route 10.10.0.0 255.255.0.0 192.0.2.1")
        self.assertEqual(p.argv, [["ip", "route", "replace", "10.10.0.0/16", "via", "192.0.2.1"]])
        self.assertTrue(p.mutating)
    def test_ios_bgp_config(self):
        p = mod.translate("ios", "configure terminal\nrouter bgp 65000\nneighbor 192.0.2.2 remote-as 65001\nend")
        self.assertIn("neighbor 192.0.2.2 remote-as 65001", p.argv[0])
        self.assertTrue(p.mutating)
    def test_ios_bgp_network_mask(self):
        p = mod.translate("ios", "configure terminal\nrouter bgp 65000\nnetwork 198.51.100.0 mask 255.255.255.0\nend")
        self.assertIn("network 198.51.100.0/24", p.argv[0])
    def test_ios_ospf_wildcard(self):
        p = mod.translate("ios", "configure terminal\nrouter ospf 10\nnetwork 10.0.0.0 0.0.0.255 area 0\nend")
        self.assertIn("network 10.0.0.0 0.0.0.255 area 0", p.argv[0])
    def test_ios_interface_with_mask(self):
        p = mod.translate("ios", "configure terminal\ninterface GigabitEthernet0/0\nip address 192.0.2.1 255.255.255.0\nend")
        self.assertIn("ip address 192.0.2.1/24", p.argv[0])
    def test_ios_ipv6_static_route(self):
        with patch.object(mod.platform, "system", return_value="Linux"):
            p = mod.translate("ios", "ipv6 route 2001:db8:1::/48 2001:db8::1")
        self.assertEqual(p.argv[0], ["ip", "route", "replace", "2001:db8:1::/48", "via", "2001:db8::1"])
    def test_windows_route_backend(self):
        with patch.object(mod.platform, "system", return_value="Windows"):
            argv = mod._route_change("add", "10.0.0.0/24", "192.0.2.1")
        self.assertEqual(argv, ["route.exe", "ADD", "10.0.0.0", "MASK", "255.255.255.0", "192.0.2.1"])
    def test_freebsd_route_backend(self):
        with patch.object(mod.platform, "system", return_value="FreeBSD"):
            argv = mod._route_change("add", "10.0.0.0/24", "192.0.2.1")
        self.assertEqual(argv, ["route", "-n", "add", "-net", "10.0.0.0/24", "192.0.2.1"])
    def test_macos_route_backend(self):
        with patch.object(mod.platform, "system", return_value="Darwin"):
            argv = mod._route_change("delete", "10.0.0.0/24")
        self.assertEqual(argv, ["route", "-n", "delete", "-net", "10.0.0.0/24"])
    def test_junos_show(self):
        p = mod.translate("junos", "show route protocol bgp")
        self.assertEqual(p.argv[0], ["vtysh", "-c", "show bgp ipv4 unicast"])
    def test_junos_static_route(self):
        with patch.object(mod.platform, "system", return_value="Linux"):
            p = mod.translate("junos", "set routing-options static route 203.0.113.0/24 next-hop 192.0.2.1")
        self.assertEqual(p.argv[0], ["ip", "route", "replace", "203.0.113.0/24", "via", "192.0.2.1"])
    def test_junos_bgp_requires_asn(self):
        with self.assertRaises(mod.CommandError):
            mod.translate("junos", "set protocols bgp group EDGE neighbor 192.0.2.1 peer-as 65001")
    def test_junos_bgp_config(self):
        p = mod.translate("junos", "set routing-options autonomous-system 65000\nset protocols bgp group EDGE neighbor 192.0.2.1 peer-as 65001")
        self.assertIn("router bgp 65000", p.argv[0])
    def test_ios_isis_requires_net(self):
        with self.assertRaises(mod.CommandError):
            mod.translate("ios", "configure terminal\nrouter isis CORE\nend")
    def test_ios_isis_net_and_interface(self):
        p = mod.translate("ios", "configure terminal\nrouter isis CORE\nnet 49.0001.0000.0000.0001.00\ninterface GigabitEthernet0/0\nip router isis CORE\nend")
        self.assertIn("net 49.0001.0000.0000.0001.00", p.argv[0])
    def test_unknown_command_rejected(self):
        with self.assertRaises(mod.CommandError): mod.translate("ios", "reload")
    def test_injection_rejected(self):
        with self.assertRaises((mod.CommandError, ValueError)):
            mod.translate("ios", "ip route 10.0.0.0 255.0.0.0 192.0.2.1; reboot")

if __name__ == "__main__": unittest.main()

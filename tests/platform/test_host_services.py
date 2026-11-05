import importlib.util
import pathlib
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("chimera_host_services",ROOT/"tools/hosted/chimera-host-services.py")
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class HostServiceTests(unittest.TestCase):
    def test_linux_systemd_status(self):
        with patch.object(mod,"host_family",return_value="linux"), patch.object(mod.shutil,"which",side_effect=lambda x:"/bin/"+x if x=="systemctl" else None):
            argv,mut=mod.plan("status","sshd")
        self.assertEqual(argv,["/bin/systemctl","status","sshd.service"])
        self.assertFalse(mut)
    def test_freebsd_rc_service(self):
        def which(x): return "/usr/sbin/"+x if x in {"service","sysrc"} else None
        with patch.object(mod,"host_family",return_value="freebsd"), patch.object(mod.shutil,"which",side_effect=which):
            argv,mut=mod.plan("enable","sshd")
        self.assertEqual(argv,["/usr/sbin/sysrc","sshd_enable=YES"])
        self.assertTrue(mut)
    def test_windows_service_control(self):
        with patch.object(mod,"host_family",return_value="windows"), patch.object(mod.shutil,"which",return_value="C:/Windows/sc.exe"):
            argv,mut=mod.plan("start","Spooler")
        self.assertEqual(argv,["C:/Windows/sc.exe","start","Spooler"])
        self.assertTrue(mut)
    def test_macos_launchd_domain(self):
        with patch.object(mod,"host_family",return_value="macos"), patch.object(mod.shutil,"which",return_value="/bin/launchctl"), patch.object(mod.os,"getuid",return_value=501,create=True):
            argv,mut=mod.plan("status","com.apple.Finder","user")
        self.assertEqual(argv,["/bin/launchctl","print","gui/501/com.apple.Finder"])
        self.assertFalse(mut)
    def test_invalid_name_rejected(self):
        with self.assertRaises(mod.ServiceError): mod.plan("start","sshd; reboot")
    def test_unknown_action_rejected(self):
        with self.assertRaises(mod.ServiceError): mod.plan("install","nginx")

if __name__=="__main__": unittest.main()

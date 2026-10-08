import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROFILES=json.loads((ROOT/"tools/virtualization/machine-profiles.json").read_text())["profiles"]
BACKENDS={b["id"]:b for b in json.loads((ROOT/"tools/virtualization/hypervisor-backends.json").read_text())["backends"]}

class QemuProfileSmokeTests(unittest.TestCase):
    def test_installed_target_machine_profiles(self):
        checked=0
        for p in PROFILES:
            b=BACKENDS[p["backend"]]
            binary=b.get("binary")
            if not binary or not b.get("enabled") or not shutil.which(binary):
                continue
            checked+=1
            result=subprocess.run([binary,"-machine","help"],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,f"{binary} -machine help failed: {result.stderr}")
            listing=result.stdout+result.stderr
            self.assertIn(p["machine"],listing,f"machine {p['machine']} not listed by {binary}")
        if checked==0:self.skipTest("No configured QEMU system binaries installed on this runner")

if __name__=="__main__": unittest.main()

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
            # Start the selected machine with vCPUs paused. This validates that QEMU
            # can initialize the configured machine/CPU; it does not boot a guest OS.
            args=[binary,"-machine",p["machine"],"-cpu",p["cpu"],"-m","128M",
                  "-audiodev","none,id=audio0","-display","none","-nodefaults","-S","-monitor","none",
                  "-serial","none","-no-reboot"]
            # Don't require a separately packaged OpenSBI firmware just to test
            # board/CPU initialization; actual guest boot tests must supply it.
            if p["backend"] in ("qemu-riscv32","qemu-riscv64"):
                args += ["-bios","none"]
            proc=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            try:
                code=proc.wait(timeout=1.5)
                stderr=proc.stderr.read() if proc.stderr else ""
                self.assertEqual(code,0,f"profile startup exited for {p['id']}: {stderr}")
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:proc.wait(timeout=3)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
            finally:
                if proc.stderr: proc.stderr.close()
        if checked==0:self.skipTest("No configured QEMU system binaries installed on this runner")

if __name__=="__main__": unittest.main()

#!/usr/bin/env python3
"""Host-only regression tests for the mobile flash tool; no real device writes."""
import hashlib, json, os, pathlib, subprocess, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "mobile/flash/mobile-flash-tool.sh"

def run(args, env=None, ok=True):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if ok and p.returncode != 0:
        raise AssertionError(f"command failed ({p.returncode}): {' '.join(map(str,args))}\n{p.stdout}")
    if not ok and p.returncode == 0:
        raise AssertionError(f"command unexpectedly succeeded: {' '.join(map(str,args))}\n{p.stdout}")
    return p

def main():
    run(["bash", "-n", str(TOOL)])
    with tempfile.TemporaryDirectory(prefix="chm-mobile-flash-test-") as td:
        d = pathlib.Path(td)
        image = d / "boot.img"
        image.write_bytes(b"test-only-mobile-image\0")
        manifest = d / "device.json"
        manifest.write_text(json.dumps({
            "schema": "CHM-MOBILE-DEVICE-2", "codename": "testphone",
            "architecture": "aarch64", "bootloader_mode": "fastboot",
            "partitions": [{"name": "boot", "image": image.name,
                            "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                            "required": True}],
            "policy": {"exact_match_required": True, "generic_partition_names_forbidden": True,
                       "signed_images_required": True, "confirmation_required": True,
                       "unlock_required": False}
        }), encoding="utf-8")
        private, public, signature = d/"key.pem", d/"key.pub", d/"manifest.sig"
        run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
             "-out", str(private)])
        run(["openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public)])
        run(["openssl", "dgst", "-sha256", "-sign", str(private), "-out", str(signature), str(manifest)])
        run(["bash", str(TOOL), "--verify", "--manifest", str(manifest),
             "--signature", str(signature), "--public-key", str(public)])

        fakebin = d/"bin"; fakebin.mkdir()
        log = d/"fastboot.log"
        fake = fakebin/"fastboot"
        fake.write_text("""#!/usr/bin/env bash
if [[ "$1" == devices ]]; then echo 'SERIAL123 fastboot'; exit 0; fi
if [[ "$1" == -s && "$3" == getvar && "$4" == product ]]; then echo '(bootloader) product: testphone'; exit 0; fi
if [[ "$1" == -s && "$3" == getvar && "$4" == unlocked ]]; then echo '(bootloader) unlocked: no'; exit 0; fi
echo "$@" >> "$CHIMERA_TEST_FASTBOOT_LOG"
exit 99
""", encoding="utf-8")
        fake.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = str(fakebin) + os.pathsep + env["PATH"]
        env["CHIMERA_TEST_FASTBOOT_LOG"] = str(log)
        dry = run(["bash", str(TOOL), "--flash", "--device", "testphone", "--serial", "SERIAL123",
                   "--manifest", str(manifest), "--signature", str(signature),
                   "--public-key", str(public), "--dry-run"], env=env)
        assert "no writes performed" in dry.stdout
        assert not log.exists(), "dry-run must not invoke a write operation"

        # A changed manifest must fail its detached signature check.
        manifest.write_text(manifest.read_text(encoding="utf-8") + " ", encoding="utf-8")
        run(["bash", str(TOOL), "--verify", "--manifest", str(manifest),
             "--signature", str(signature), "--public-key", str(public)], ok=False)
    print("mobile flash tool syntax, signature, digest, exact-device and dry-run tests: PASS")

if __name__ == "__main__":
    main()

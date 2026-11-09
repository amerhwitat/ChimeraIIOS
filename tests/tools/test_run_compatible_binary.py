import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("chm_run_binary",ROOT/"tools/run-compatible-binary.py")
MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)

class RuntimeSelectionTests(unittest.TestCase):
    def fake_which(self,*available):
        return lambda name: "/usr/bin/"+name if name in available else None

    def test_pe_header_after_first_page_is_inspected(self):
        import struct
        import tempfile
        data = bytearray(8192 + 256)
        data[:2] = b"MZ"
        data[0x3C:0x40] = struct.pack("<I", 8192)
        data[8192:8196] = b"PE\\0\\0"
        data[8196:8198] = struct.pack("<H", 0x8664)
        data[8198:8200] = struct.pack("<H", 3)
        data[8192 + 20:8192 + 22] = struct.pack("<H", 0xF0)
        opt = 8192 + 24
        data[opt:opt + 2] = struct.pack("<H", 0x20B)
        data[opt + 68:opt + 70] = struct.pack("<H", 3)
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "delayed-header.exe"
            binary.write_bytes(data)
            report = MODULE.inspect_binary(binary)
        self.assertEqual(report["format"], "PE/COFF")
        self.assertEqual(report["architecture"], "x86_64")
        self.assertEqual(report["subsystem"], "windows-console")

    def test_native_linux(self):
        report={"format":"ELF","architecture":"x86_64"}
        command,mode=MODULE.choose_command(report,Path("/tmp/app"),("Linux","x86_64"),self.fake_which())
        self.assertEqual(mode,"native-linux");self.assertEqual(command[0],"/tmp/app")

    def test_foreign_linux_uses_qemu(self):
        report={"format":"ELF","architecture":"AArch64"}
        command,mode=MODULE.choose_command(report,Path("/tmp/app"),("Linux","x86_64"),self.fake_which("qemu-aarch64"),sysroot="/usr/aarch64-linux-gnu")
        self.assertEqual(mode,"qemu-user");self.assertEqual(command[:3],["/usr/bin/qemu-aarch64","-L","/usr/aarch64-linux-gnu"])

    def test_windows_pe_uses_wine(self):
        report={"format":"PE/COFF","architecture":"x86_64"}
        command,mode=MODULE.choose_command(report,Path("/tmp/app.exe"),("Linux","x86_64"),self.fake_which("wine"))
        self.assertEqual(mode,"wine-compat");self.assertEqual(command[0],"/usr/bin/wine")

    def test_riscv32_and_little_endian_mips(self):
        rv={"format":"ELF","architecture":"RISC-V","bits":32,"endianness":"little"}
        cmd,mode=MODULE.choose_command(rv,Path("/tmp/app"),("Linux","x86_64"),self.fake_which("qemu-riscv32"))
        self.assertEqual((cmd[0],mode),("/usr/bin/qemu-riscv32","qemu-user"))
        mips={"format":"ELF","architecture":"MIPS","bits":32,"endianness":"little"}
        cmd,mode=MODULE.choose_command(mips,Path("/tmp/app"),("Linux","x86_64"),self.fake_which("qemu-mipsel"))
        self.assertEqual((cmd[0],mode),("/usr/bin/qemu-mipsel","qemu-user"))

    def test_macos_requires_macos_host(self):
        report={"format":"Mach-O","architecture":"AArch64"}
        with self.assertRaises(RuntimeError):
            MODULE.choose_command(report,Path("/tmp/app"),("Linux","x86_64"),self.fake_which())

    def test_dos_uses_dosbox(self):
        report={"format":"DOS MZ","architecture":"x86"}
        command,mode=MODULE.choose_command(report,Path("/tmp/APP.EXE"),("Linux","x86_64"),self.fake_which("dosbox"))
        self.assertEqual(mode,"dosbox-emulation");self.assertEqual(command[0],"/usr/bin/dosbox")

    def test_wasm_uses_wasmtime(self):
        report={"format":"WebAssembly","architecture":"wasm"}
        command,mode=MODULE.choose_command(report,Path("/tmp/app.wasm"),("Linux","x86_64"),self.fake_which("wasmtime"))
        self.assertEqual(mode,"wasmtime");self.assertEqual(command[1],"run")

if __name__=="__main__":unittest.main()

#!/usr/bin/env python3
"""Host regression tests for ELF admission validation and scheduler transitions."""
import ctypes
import pathlib
import struct
import subprocess
import tempfile
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

class Info(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("cpu", ctypes.c_uint32),
                ("state", ctypes.c_uint32), ("priority", ctypes.c_uint32),
                ("affinity_mask", ctypes.c_uint64), ("runs", ctypes.c_uint64),
                ("ticks", ctypes.c_uint64)]
class Segment(ctypes.Structure):
    _fields_ = [("file_offset", ctypes.c_uint64), ("virtual_address", ctypes.c_uint64),
                ("file_size", ctypes.c_uint64), ("memory_size", ctypes.c_uint64),
                ("flags", ctypes.c_uint64), ("align", ctypes.c_uint64),
                ("page_offset", ctypes.c_uint64)]
class Proc(ctypes.Structure):
    _fields_ = [("pid", ctypes.c_uint32), ("state", ctypes.c_uint32),
                ("segment_count", ctypes.c_uint32), ("reserved", ctypes.c_uint32),
                ("entry", ctypes.c_uint64), ("user_stack_top", ctypes.c_uint64),
                ("image_low", ctypes.c_uint64), ("image_high", ctypes.c_uint64),
                ("segments", Segment * 16)]

class Mode(ctypes.Structure):
    _fields_ = [("process_id", ctypes.c_uint32), ("mode_bits", ctypes.c_uint32),
                ("guest_isa", ctypes.c_uint32), ("execution_class", ctypes.c_int),
                ("compatibility_target", ctypes.c_uint32), ("abi_version", ctypes.c_uint32),
                ("flags", ctypes.c_uint32)]

class KernelContracts(unittest.TestCase):
    def test_x86_user_mode_fails_closed_without_nx(self):
        # NX is a security prerequisite, not an optional optimization: without
        # EFER.NXE, data and stack pages could remain executable.
        source = (ROOT / "kernel/core/user_mode.cpp").read_text()
        self.assertIn("if(!nx_available) return -3;", source)
        self.assertIn("if(nx_available&&!(permissions&CHIMERA_ELF_EXEC)) flags|=NX;", source)

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.lib = pathlib.Path(cls.tmp.name) / "libkoronos_contracts.so"
        subprocess.run([
            "g++", "-std=c++17", "-shared", "-fPIC", "-pthread",
            "-I", str(ROOT / "kernel/include"),
            str(ROOT / "kernel/core/process.cpp"),
            str(ROOT / "kernel/core/elf_loader.cpp"),
            str(ROOT / "kernel/core/nbit.cpp"),
            str(ROOT / "kernel/core/hardware.cpp"),
            str(ROOT / "kernel/core/ipc.cpp"),
            str(ROOT / "kernel/core/scheduler.cpp"), "-o", str(cls.lib),
        ], check=True)
        cls.api = ctypes.CDLL(str(cls.lib))
        cls.api.chimera_sched_submit.argtypes = [CALLBACK, ctypes.c_void_p, ctypes.c_uint32]
        cls.api.chimera_sched_submit.restype = ctypes.c_int
        cls.api.chimera_sched_run_once.argtypes = [ctypes.c_uint32]
        cls.api.chimera_sched_run_once.restype = ctypes.c_uint32
        cls.api.chimera_sched_snapshot.argtypes = [ctypes.POINTER(Info), ctypes.c_uint32]
        cls.api.chimera_sched_snapshot.restype = ctypes.c_uint32
        cls.api.chimera_process_admit_elf.argtypes = [ctypes.c_void_p, ctypes.c_uint64,
            ctypes.c_uint16, ctypes.c_uint64, ctypes.POINTER(Proc)]
        cls.api.chimera_process_admit_elf.restype = ctypes.c_int
        cls.api.chimera_process_set_execution_mode.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
        cls.api.chimera_process_set_execution_mode.restype = ctypes.c_int
        cls.api.chimera_process_set_state.argtypes = [ctypes.c_uint32, ctypes.c_int]
        cls.api.chimera_process_set_state.restype = ctypes.c_int
        cls.api.chimera_nbit_process_get.argtypes = [ctypes.c_uint32, ctypes.POINTER(Mode)]
        cls.api.chimera_nbit_process_get.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @staticmethod
    def elf_fixture(flags=5, entry=0x400000, align=1, phoff=64, size=256):
        image = bytearray(size)
        image[0:7] = b"\x7fELF\x02\x01\x01"
        struct.pack_into("<HHIQQQIHHHHHH", image, 16,
                         2, 62, 1, entry, phoff, 0, 0, 64, 56, 1, 64, 0, 0)
        if phoff + 56 <= size:
            struct.pack_into("<IIQQQQQQ", image, phoff,
                             1, flags, 120, 0x400000, 0, 4, 16, align)
        image[120:124] = b"TEST"
        return image

    def admit(self, image):
        buf = ctypes.create_string_buffer(bytes(image))
        out = Proc()
        result = self.api.chimera_process_admit_elf(
            buf, len(image), 62, 0x70000000, ctypes.byref(out))
        return result, out

    def test_process_mode_registry_tracks_admission_compatibility_and_exit(self):
        result, proc = self.admit(self.elf_fixture())
        self.assertGreater(result, 0)
        mode = Mode()
        self.assertEqual(self.api.chimera_nbit_process_get(result, ctypes.byref(mode)), 0)
        self.assertEqual(mode.mode_bits, 64)
        # CHIMERA_COMPAT_LINUX is bit 2 in the public hardware ABI.
        self.assertEqual(self.api.chimera_process_set_execution_mode(result, 32, 1 << 2), 0)
        self.assertEqual(self.api.chimera_nbit_process_get(result, ctypes.byref(mode)), 0)
        self.assertEqual(mode.mode_bits, 32)
        self.assertEqual(mode.execution_class, 2)  # CHIMERA_EXEC_COMPATIBILITY
        self.assertEqual(self.api.chimera_process_set_state(result, 5), 0)  # EXITED
        self.assertNotEqual(self.api.chimera_nbit_process_get(result, ctypes.byref(mode)), 0)

    def test_block_wake_is_bound_to_selected_cpu_task(self):
        api = self.api
        api.chimera_sched_init(2)
        seen = ctypes.c_uint32(0)
        @CALLBACK
        def callback(_):
            seen.value += 1
            api.chimera_sched_block_cpu(0)
        task_id = api.chimera_sched_submit(callback, None, 1)
        self.assertGreater(task_id, 0)
        self.assertEqual(api.chimera_sched_run_once(0), 1)
        self.assertEqual(seen.value, 1)
        snapshot = (Info * 8)()
        self.assertEqual(api.chimera_sched_snapshot(snapshot, 8), 1)
        self.assertEqual(snapshot[0].state, 2)
        api.chimera_sched_wake(task_id)
        self.assertEqual(api.chimera_sched_snapshot(snapshot, 8), 1)
        self.assertEqual(snapshot[0].state, 0)

    def test_running_task_cannot_be_redispatched_after_yield_until_callback_returns(self):
        api = self.api
        api.chimera_sched_init(2)
        entered, release = threading.Event(), threading.Event()
        @CALLBACK
        def callback(_):
            api.chimera_sched_yield_cpu(0)
            entered.set()
            release.wait(timeout=5)
        api.chimera_sched_submit(callback, None, 1)
        worker = threading.Thread(target=lambda: api.chimera_sched_run_once(0))
        worker.start()
        self.assertTrue(entered.wait(timeout=5))
        try:
            self.assertEqual(api.chimera_sched_run_once(1), 0)
        finally:
            release.set()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())

    def test_scheduler_never_dispatches_one_task_twice_in_nested_call(self):
        api = self.api
        api.chimera_sched_init(2)
        observed, nested_results = [], []
        @CALLBACK
        def callback(_):
            observed.append(1)
            nested_results.append(api.chimera_sched_run_once(0))
        api.chimera_sched_submit(callback, None, 1)
        self.assertEqual(api.chimera_sched_run_once(0), 1)
        self.assertEqual(observed, [1])
        self.assertEqual(nested_results, [0])

    def test_elf_accepts_valid_executable_load_plan(self):
        self.api.chimera_process_init()
        result, out = self.admit(self.elf_fixture())
        self.assertGreater(result, 0)
        self.assertEqual(out.segment_count, 1)
        self.assertEqual(out.entry, 0x400000)
        self.assertEqual(out.user_stack_top, 0x70000000)
        self.assertEqual(out.segments[0].page_offset, 0)

    def test_elf_rejects_truncated_program_header_table(self):
        self.api.chimera_process_init()
        image = bytearray(128)
        image[0:7] = b"\x7fELF\x02\x01\x01"
        struct.pack_into("<HHIQQQIHHHHHH", image, 16,
                         2, 62, 1, 0x400000, 120, 0, 0, 64, 56, 2, 64, 0, 0)
        result, _ = self.admit(image)
        self.assertLess(result, 0)

    def test_elf_rejects_writable_executable_segment(self):
        self.api.chimera_process_init()
        result, _ = self.admit(self.elf_fixture(flags=7))
        self.assertLess(result, 0)

    def test_elf_rejects_entry_outside_executable_segment(self):
        self.api.chimera_process_init()
        result, _ = self.admit(self.elf_fixture(flags=4, entry=0x500000))
        self.assertLess(result, 0)

if __name__ == "__main__":
    unittest.main()

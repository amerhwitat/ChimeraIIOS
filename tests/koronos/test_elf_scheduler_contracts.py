#!/usr/bin/env python3
"""Host regression tests for ELF admission validation and scheduler transitions."""
import ctypes
import pathlib
import struct
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class Info(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("cpu", ctypes.c_uint32),
                ("state", ctypes.c_uint32), ("priority", ctypes.c_uint32),
                ("affinity_mask", ctypes.c_uint64), ("runs", ctypes.c_uint64),
                ("ticks", ctypes.c_uint64)]

class Segment(ctypes.Structure):
    _fields_ = [("file_offset", ctypes.c_uint64), ("virtual_address", ctypes.c_uint64),
                ("file_size", ctypes.c_uint64), ("memory_size", ctypes.c_uint64),
                ("flags", ctypes.c_uint64), ("align", ctypes.c_uint64)]

class Proc(ctypes.Structure):
    _fields_ = [("pid", ctypes.c_uint32), ("state", ctypes.c_uint32),
                ("segment_count", ctypes.c_uint32), ("reserved", ctypes.c_uint32),
                ("entry", ctypes.c_uint64), ("user_stack_top", ctypes.c_uint64),
                ("image_low", ctypes.c_uint64), ("image_high", ctypes.c_uint64),
                ("segments", Segment * 16)]

class KernelContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.lib = pathlib.Path(cls.tmp.name) / "libkoronos_contracts.so"
        subprocess.run([
            "g++", "-std=c++17", "-shared", "-fPIC", "-pthread",
            "-I", str(ROOT / "kernel/include"),
            str(ROOT / "kernel/core/process.cpp"),
            str(ROOT / "kernel/core/scheduler.cpp"), "-o", str(cls.lib),
        ], check=True)
        cls.api = ctypes.CDLL(str(cls.lib))
        cls.api.chimera_sched_submit.argtypes = [ctypes.CFUNCTYPE(None, ctypes.c_void_p),
                                                 ctypes.c_void_p, ctypes.c_uint32]
        cls.api.chimera_sched_submit.restype = ctypes.c_int
        cls.api.chimera_sched_run_once.argtypes = [ctypes.c_uint32]
        cls.api.chimera_sched_run_once.restype = ctypes.c_uint32
        cls.api.chimera_sched_snapshot.argtypes = [ctypes.POINTER(Info), ctypes.c_uint32]
        cls.api.chimera_sched_snapshot.restype = ctypes.c_uint32
        cls.api.chimera_process_admit_elf.argtypes = [ctypes.c_void_p, ctypes.c_uint64,
            ctypes.c_uint16, ctypes.c_uint64, ctypes.POINTER(Proc)]
        cls.api.chimera_process_admit_elf.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_block_wake_is_bound_to_selected_cpu_task(self):
        api = self.api
        api.chimera_sched_init(2)
        seen = ctypes.c_uint32(0)
        callback_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
        @callback_type
        def callback(_):
            seen.value += 1
            api.chimera_sched_block_cpu(0)
        task_id = api.chimera_sched_submit(callback, None, 1)
        self.assertGreater(task_id, 0)
        self.assertEqual(api.chimera_sched_run_once(0), 1)
        self.assertEqual(seen.value, 1)
        snapshot = (Info * 8)()
        self.assertEqual(api.chimera_sched_snapshot(snapshot, 8), 1)
        self.assertEqual(snapshot[0].state, 2)  # BLOCKED persists after callback return
        api.chimera_sched_wake(task_id)
        self.assertEqual(api.chimera_sched_snapshot(snapshot, 8), 1)
        self.assertEqual(snapshot[0].state, 0)  # READY after wake

    def test_scheduler_never_dispatches_one_task_twice_in_nested_call(self):
        api = self.api
        api.chimera_sched_init(2)
        observed = []
        callback_type = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
        @callback_type
        def callback(_):
            observed.append(1)
            # CPU 0 is still executing this task, so nested dispatch on CPU 0
            # must refuse to run it again.
            self.assertEqual(api.chimera_sched_run_once(0), 0)
        api.chimera_sched_submit(callback, None, 1)
        self.assertEqual(api.chimera_sched_run_once(0), 1)
        self.assertEqual(len(observed), 1)

    def test_elf_rejects_truncated_program_header_table(self):
        api = self.api
        api.chimera_process_init()
        image = bytearray(128)
        image[0:4] = b"\x7fELF"
        image[4] = 2; image[5] = 1; image[6] = 1
        struct.pack_into("<HHIQQQIHHHHHH", image, 16,
                         2, 62, 1, 0x400000, 120, 0, 0, 64, 56, 2, 64, 0, 0)
        buf = ctypes.create_string_buffer(bytes(image))
        out = Proc()
        self.assertLess(api.chimera_process_admit_elf(
            buf, len(image), 62, 0x70000000, ctypes.byref(out)), 0)

if __name__ == "__main__":
    unittest.main()

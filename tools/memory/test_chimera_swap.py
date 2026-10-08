import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chimera_swap import SwapArea, SwapError, PAGE, HEADER, META


class SwapTests(unittest.TestCase):
    def test_roundtrip_clear_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "swap.bin"
            swap = SwapArea.create(path, 2)
            data = bytes(i % 251 for i in range(PAGE))
            swap.write_page(1, data)
            self.assertEqual(swap.read_page(1), data)
            swap.clear(1)
            with self.assertRaises(SwapError):
                swap.read_page(1)
            with self.assertRaises(SwapError):
                swap.read_page(2)
            swap.close()

    def test_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "swap.bin"
            swap = SwapArea.create(path, 1)
            swap.write_page(0, b"x" * PAGE)
            swap.close()
            with open(path, "r+b") as file:
                file.seek(HEADER.size + META.size)
                file.write(b"y")
            swap = SwapArea(path)
            with self.assertRaises(SwapError):
                swap.read_page(0)
            swap.close()


if __name__ == "__main__":
    unittest.main()

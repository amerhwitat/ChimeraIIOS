import tempfile
import unittest
from pathlib import Path
from chimera_storage import ImageRaid, pack_block, unpack_block


class StorageReferenceTests(unittest.TestCase):
    def images(self, directory, count=2, size=4096):
        paths = [Path(directory) / f"member{i}.img" for i in range(count)]
        for path in paths:
            path.write_bytes(bytes(size))
        return paths

    def test_raid1_mirrors_and_reads(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.images(d)
            with ImageRaid(paths, level=1) as raid:
                payload = b"A" * 512
                raid.write(2, payload)
                self.assertEqual(raid.read(2), payload)
            self.assertEqual(paths[0].read_bytes()[1024:1536], paths[1].read_bytes()[1024:1536])

    def test_raid0_stripes_logical_sectors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.images(d)
            with ImageRaid(paths, level=0) as raid:
                raid.write(0, b"A" * 512 + b"B" * 512)
                self.assertEqual(raid.read(0, 2), b"A" * 512 + b"B" * 512)
            self.assertEqual(paths[0].read_bytes()[:512], b"A" * 512)
            self.assertEqual(paths[1].read_bytes()[:512], b"B" * 512)

    def test_raid_rejects_out_of_range(self):
        with tempfile.TemporaryDirectory() as d:
            with ImageRaid(self.images(d), level=1) as raid:
                with self.assertRaises(ValueError):
                    raid.read(raid.sectors)

    def test_compression_round_trip_and_corruption(self):
        frame = pack_block(b"hello" * 2000)
        self.assertEqual(unpack_block(frame), b"hello" * 2000)
        damaged = frame[:-1] + bytes([frame[-1] ^ 1])
        with self.assertRaises(ValueError):
            unpack_block(damaged)

    def test_decompression_limit(self):
        frame = pack_block(b"X" * 10000)
        with self.assertRaises(ValueError):
            unpack_block(frame, max_output=100)


if __name__ == "__main__":
    unittest.main()

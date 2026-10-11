#!/usr/bin/env python3
import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
class Contracts(unittest.TestCase):
 def test_dma_masks_and_nbit_separation(self):
  h=(ROOT/"kernel/include/chimera/dma.h").read_text()
  c=(ROOT/"kernel/core/dma.cpp").read_text()
  self.assertIn("dma_mask",h); self.assertIn("address_bits",h)
  self.assertIn("logical<hardware?logical:hardware",c)
  self.assertIn("valid(p,n,d->dma_mask)",c)
 def test_dbus_requires_userspace_bridge(self):
  h=(ROOT/"kernel/include/chimera/dbus_compat.h").read_text()
  d=(ROOT/"docs/koronos-linux-dbus-and-nbit-dma.md").read_text()
  self.assertIn("userspace libdbus/sd-bus proxy is required",h)
  self.assertIn("userspace proxy",d)
if __name__=="__main__": unittest.main()

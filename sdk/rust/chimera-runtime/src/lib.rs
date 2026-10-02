#![allow(dead_code)]

pub const LOGICAL_BITS: usize = 8192;

#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct ChimeraNBit<const LIMBS: usize> {
    pub limbs: [u64; LIMBS],
}

impl<const LIMBS: usize> ChimeraNBit<LIMBS> {
    pub const fn zero() -> Self { Self { limbs: [0; LIMBS] } }
}

#[no_mangle]
pub extern "C" fn chimera_runtime_version() -> u32 { 1 }

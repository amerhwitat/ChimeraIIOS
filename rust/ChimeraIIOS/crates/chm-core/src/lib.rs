pub const CHIMERA_VERSION: &str = "2.6-rust-research";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Arch { X86_64, Arm64, RiscV64, R8192 }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RuntimeMode { Classical, HybridQuantum, Experimental128D }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CapabilityProfile {
    pub arch: Arch,
    pub quantum_simulator: bool,
    pub accelerator: bool,
    pub dimensions: usize,
}

impl CapabilityProfile {
    pub const fn research_default(arch: Arch) -> Self {
        Self { arch, quantum_simulator: true, accelerator: false, dimensions: 128 }
    }
}

//! Chimera II ISA catalog adapter. Canonical instruction data lives in isa/catalog.json.
pub const CATALOG_VERSION: &str = "CHM-ISA-CATALOG-1";
pub const CATALOG_PATH: &str = "isa/catalog.json";
#[derive(Debug, Clone, Copy)]
pub struct InstructionRef<'a> { pub id: &'a str, pub family: &'a str, pub mnemonic: &'a str, pub syntax: &'a str, pub hex: &'a str }

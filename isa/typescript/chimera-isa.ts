export const CHM_ISA_CATALOG_VERSION = "CHM-ISA-CATALOG-1" as const;
export const CHM_ISA_CATALOG_PATH = "isa/catalog.json" as const;
export type InstructionRef = { id: string; family: string; mnemonic: string; syntax: string; hex: string };

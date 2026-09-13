class ChimeraISA {
  static const catalogVersion = 'CHM-ISA-CATALOG-1';
  static const catalogPath = 'isa/catalog.json';
}
class InstructionRef {
  final String id, family, mnemonic, syntax, hex;
  const InstructionRef(this.id, this.family, this.mnemonic, this.syntax, this.hex);
}

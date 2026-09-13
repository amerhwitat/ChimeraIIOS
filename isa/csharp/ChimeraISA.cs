namespace Chimera.ISA;
public static class ChimeraISA {
    public const string CatalogVersion = "CHM-ISA-CATALOG-1";
    public const string CatalogPath = "isa/catalog.json";
    public readonly record struct InstructionRef(string Id, string Family, string Mnemonic, string Syntax, string Hex);
}

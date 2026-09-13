package chimera.isa;
/** Canonical ISA metadata is in ../catalog.json. */
public final class ChimeraISA {
  public static final String CATALOG_VERSION = "CHM-ISA-CATALOG-1";
  public static final String CATALOG_PATH = "isa/catalog.json";
  public record InstructionRef(String id, String family, String mnemonic, String syntax, String hex) {}
  private ChimeraISA() {}
}

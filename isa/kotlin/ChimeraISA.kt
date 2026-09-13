package chimera.isa
object ChimeraISA {
    const val CATALOG_VERSION = "CHM-ISA-CATALOG-1"
    const val CATALOG_PATH = "isa/catalog.json"
    data class InstructionRef(val id: String, val family: String, val mnemonic: String, val syntax: String, val hex: String)
}

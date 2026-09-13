#ifndef CHM_ISA_H
#define CHM_ISA_H
#define CHM_ISA_CATALOG_VERSION "CHM-ISA-CATALOG-1"
#define CHM_ISA_CATALOG_PATH "isa/catalog.json"
/* Canonical instruction/operand/encoding data is stored in catalog.json. */
typedef struct { const char *id; const char *family; const char *mnemonic; const char *syntax; const char *hex; } chm_isa_instruction_ref;
#endif

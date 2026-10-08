#pragma once
#include <stdint.h>
struct chimera_isa_info { const char* architecture; const char* mnemonic; const char* opcode; uint16_t bits; };
extern "C" void chimera_isa_init(void);
extern "C" uint32_t chimera_isa_count(void);
extern "C" const void* chimera_isa_find(const char* architecture, const char* mnemonic);
extern "C" const void* chimera_isa_find_opcode(const char* architecture, const char* opcode);

/* Catalogued worked samples expose their exact bits; this is not a decoder. */
struct chimera_isa_sample_info { const char* family; const char* mnemonic; const char* syntax; const char* binary; const char* hex; uint16_t bits; };
extern "C" uint32_t chimera_isa_sample_count(void);
extern "C" const void* chimera_isa_find_sample(const char* family, const char* mnemonic);

struct chimera_isa_encoding_template_info { const char* architecture; const char* family; const char* mnemonic; const char* form; const char* syntax; const char* binary; const char* hex; const char* mask_binary; const char* mask_hex; uint16_t bits; };
extern "C" uint32_t chimera_isa_encoding_template_count(void);
extern "C" const void* chimera_isa_find_encoding_template(const char* architecture, const char* mnemonic);

#include "chimera/isa_registry.h"
#include "../generated/chimera_isa_registry.generated.h"
#include "../generated/chimera_isa_encoding_samples.generated.h"
static int eq(const char*a,const char*b){if(!a||!b)return 0;while(*a&&*b){if(*a++!=*b++)return 0;}return *a==0&&*b==0;}
extern "C" void chimera_isa_init(void){}
extern "C" uint32_t chimera_isa_count(void){return CHIMERA_ISA_REGISTRY_COUNT;}
extern "C" const void* chimera_isa_find(const char* architecture,const char* mnemonic){for(uint32_t i=0;i<CHIMERA_ISA_REGISTRY_COUNT;i++)if(eq(CHIMERA_ISA_REGISTRY[i].architecture,architecture)&&eq(CHIMERA_ISA_REGISTRY[i].mnemonic,mnemonic))return &CHIMERA_ISA_REGISTRY[i];return (const void*)0;}
extern "C" const void* chimera_isa_find_opcode(const char* architecture,const char* opcode){for(uint32_t i=0;i<CHIMERA_ISA_REGISTRY_COUNT;i++)if(eq(CHIMERA_ISA_REGISTRY[i].architecture,architecture)&&eq(CHIMERA_ISA_REGISTRY[i].opcode,opcode))return &CHIMERA_ISA_REGISTRY[i];return (const void*)0;}

extern "C" uint32_t chimera_isa_sample_count(void){return CHIMERA_ISA_SAMPLE_COUNT;}
extern "C" const void* chimera_isa_find_sample(const char* family,const char* mnemonic){for(uint32_t i=0;i<CHIMERA_ISA_SAMPLE_COUNT;i++)if(eq(CHIMERA_ISA_SAMPLES[i].family,family)&&eq(CHIMERA_ISA_SAMPLES[i].mnemonic,mnemonic))return &CHIMERA_ISA_SAMPLES[i];return (const void*)0;}

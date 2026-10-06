#pragma once
#include <stdint.h>
extern "C" void chimera_ai_model_init(void);
extern "C" uint64_t chimera_ai_event_count(void);
extern "C" int chimera_ai_record_event(const char* page,const char* element,const char* action);
extern "C" const char* chimera_ai_provider(void);

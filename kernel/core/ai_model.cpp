#include "chimera/ai_model.h"
static volatile uint64_t g_ai_events=0;
static const char* g_provider="browser-rnn/authorized-backend";
extern "C" void chimera_ai_model_init(void){g_ai_events=0;}
extern "C" uint64_t chimera_ai_event_count(void){return g_ai_events;}
extern "C" int chimera_ai_record_event(const char*,const char*,const char*){++g_ai_events;return 0;}
extern "C" const char* chimera_ai_provider(void){return g_provider;}

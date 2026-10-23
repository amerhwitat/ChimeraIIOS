#include "../include/chimera/service.h"
namespace {
constexpr uint32_t MAX_SERVICES = 64u;
struct service_state { const char* id; uint32_t state; };
static service_state g_states[MAX_SERVICES];
static uint32_t g_state_count = 0;
static bool same(const char* a,const char* b){if(!a||!b)return false;while(*a&&*b&&*a==*b){++a;++b;}return *a==0&&*b==0;}
static bool nonempty(const char* s){return s&&*s;}
static int find(const chimera_service_manifest*s,uint32_t n,const char*id){if(!s||!nonempty(id))return -1;for(uint32_t i=0;i<n;++i)if(same(s[i].id,id))return (int)i;return -1;}
}
extern "C" int chimera_service_validate(const chimera_service_manifest*s,uint32_t n){
 if(!s||!n)return -1;if(n>MAX_SERVICES)return -5;
 for(uint32_t i=0;i<n;++i){
  if(s[i].abi_version!=CHIMERA_SERVICE_ABI||!nonempty(s[i].id))return -2;
  if(s[i].state>CHM_SVC_RECOVERING||s[i].restart>CHM_RESTART_FAILURE||s[i].critical>1u)return -6;
  if(s[i].dependency_count&&!s[i].dependencies)return -7;
  /* A service cannot depend on itself; cap the list before dereferencing it. */
  if(s[i].dependency_count>=n)return -7;
  for(uint32_t j=i+1;j<n;++j)if(same(s[i].id,s[j].id))return -3;
  for(uint32_t d=0;d<s[i].dependency_count;++d){
   const char*dep=s[i].dependencies[d];if(!nonempty(dep)||find(s,n,dep)<0)return -4;
   if(same(s[i].id,dep))return -6;
   for(uint32_t k=0;k<d;++k)if(same(s[i].dependencies[k],dep))return -6;
  }
 }
 return 0;
}
extern "C" int chimera_service_resolve(const chimera_service_manifest*s,uint32_t n,chimera_service_plan*p){
 if(!p)return -1;p->count=0;if(!p->ordered_ids||!n||n>MAX_SERVICES||p->capacity<n)return -1;
 int rc=chimera_service_validate(s,n);if(rc<0)return rc;uint8_t done[MAX_SERVICES]={};
 while(p->count<n){bool progressed=false;for(uint32_t i=0;i<n;++i){if(done[i])continue;bool ready=true;
  for(uint32_t d=0;d<s[i].dependency_count;++d){int k=find(s,n,s[i].dependencies[d]);if(k<0||!done[(uint32_t)k]){ready=false;break;}}
  if(ready){done[i]=1;p->ordered_ids[p->count++]=s[i].id;progressed=true;}
 }if(!progressed){p->count=0;return -6;}}
 return 0;
}
extern "C" int chimera_service_set_state(const char*id,uint32_t state){
 if(!nonempty(id)||state>CHM_SVC_RECOVERING)return -1;
 for(uint32_t i=0;i<g_state_count;++i)if(same(g_states[i].id,id)){g_states[i].state=state;return 0;}
 if(g_state_count>=MAX_SERVICES)return -2;g_states[g_state_count++]={id,state};return 0;
}
extern "C" uint32_t chimera_service_get_state(const char*id){for(uint32_t i=0;i<g_state_count;++i)if(same(g_states[i].id,id))return g_states[i].state;return CHM_SVC_DECLARED;}
extern "C" void chimera_kore_bootstrap(void){
 /* Registration is not a health check. Registry initialization is not subsystem
    health; keep unimplemented services blocked until their implementations report healthy. */
 chimera_service_set_state("chimera.device",CHM_SVC_BLOCKED);
 chimera_service_set_state("chimera.storage",CHM_SVC_BLOCKED);
 chimera_service_set_state("chimera.security",CHM_SVC_BLOCKED);
 chimera_service_set_state("chimera.logging",CHM_SVC_BLOCKED);
 chimera_service_set_state("chimera.kore",CHM_SVC_RUNNING);
}

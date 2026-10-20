#include "../include/chimera/service.h"
namespace {
struct service_state { const char* id; uint32_t state; };
static service_state g_states[CHIMERA_SERVICE_MAX];
static uint32_t g_state_count=0;
static bool same(const char*a,const char*b){if(!a||!b)return false;while(*a&&*b&&*a==*b){++a;++b;}return *a==0&&*b==0;}
static int find(const chimera_service_manifest*s,uint32_t n,const char*id){if(!s||!id)return -1;for(uint32_t i=0;i<n;++i)if(same(s[i].id,id))return (int)i;return -1;}
static bool dependencies_running(const chimera_service_manifest*s,uint32_t i){for(uint32_t d=0;d<s[i].dependency_count;++d)if(chimera_service_get_state(s[i].dependencies[d])!=CHM_SVC_RUNNING)return false;return true;}
static int run_one(const char*id,const chimera_service_ops*ops){if(ops->start(id,ops->context)!=0){if(ops->stop)(void)ops->stop(id,ops->context);return -1;}if(ops->health(id,ops->context)!=0){if(ops->stop)(void)ops->stop(id,ops->context);return -2;}return 0;}
}
extern "C" int chimera_service_validate(const chimera_service_manifest*s,uint32_t n){
 if(!s||!n||n>CHIMERA_SERVICE_MAX)return -1;
 for(uint32_t i=0;i<n;++i){if(s[i].abi_version!=CHIMERA_SERVICE_ABI||!s[i].id||s[i].restart>CHM_RESTART_FAILURE||(s[i].dependency_count&&!s[i].dependencies)||s[i].dependency_count>n)return -2;
  for(uint32_t j=i+1;j<n;++j)if(same(s[i].id,s[j].id))return -3;
  for(uint32_t d=0;d<s[i].dependency_count;++d)if(!s[i].dependencies[d]||find(s,n,s[i].dependencies[d])<0)return -4;
 }return 0;
}
extern "C" int chimera_service_resolve(const chimera_service_manifest*s,uint32_t n,chimera_service_plan*p){
 if(!p||!p->ordered_ids||n>CHIMERA_SERVICE_MAX||p->capacity<n)return -1;int v=chimera_service_validate(s,n);if(v<0)return v;
 uint8_t done[CHIMERA_SERVICE_MAX]={};p->count=0;
 while(p->count<n){bool progressed=false;for(uint32_t i=0;i<n;++i){if(done[i])continue;bool ready=true;
  for(uint32_t d=0;d<s[i].dependency_count;++d){int k=find(s,n,s[i].dependencies[d]);if(k<0||!done[(uint32_t)k]){ready=false;break;}}
  if(ready){done[i]=1;p->ordered_ids[p->count++]=s[i].id;progressed=true;}}
  if(!progressed)return -6;
 }return 0;
}
extern "C" int chimera_service_set_state(const char*id,uint32_t state){
 if(!id||state>CHM_SVC_RECOVERING)return -1;for(uint32_t i=0;i<g_state_count;++i)if(same(g_states[i].id,id)){g_states[i].state=state;return 0;}
 if(g_state_count>=CHIMERA_SERVICE_MAX)return -2;g_states[g_state_count++]={id,state};return 0;
}
extern "C" uint32_t chimera_service_get_state(const char*id){for(uint32_t i=0;i<g_state_count;++i)if(same(g_states[i].id,id))return g_states[i].state;return CHM_SVC_DECLARED;}
extern "C" int chimera_service_start_all(const chimera_service_manifest*s,uint32_t n,const chimera_service_ops*ops,chimera_service_plan*p){
 if(!ops||!ops->start||!ops->health||!p)return -1;int rc=chimera_service_resolve(s,n,p);if(rc<0)return rc;
 for(uint32_t i=0;i<n;++i)(void)chimera_service_set_state(s[i].id,CHM_SVC_DECLARED);
 for(uint32_t k=0;k<p->count;++k){int idx=find(s,n,p->ordered_ids[k]);if(idx<0)return -7;const chimera_service_manifest*svc=&s[(uint32_t)idx];
  if(!dependencies_running(s,(uint32_t)idx)){(void)chimera_service_set_state(svc->id,CHM_SVC_BLOCKED);if(svc->critical)return -8;continue;}
  (void)chimera_service_set_state(svc->id,CHM_SVC_STARTING);rc=run_one(svc->id,ops);
  if(rc<0&&svc->restart==CHM_RESTART_FAILURE){(void)chimera_service_set_state(svc->id,CHM_SVC_RECOVERING);rc=run_one(svc->id,ops);}
  if(rc==0)(void)chimera_service_set_state(svc->id,CHM_SVC_RUNNING);else{(void)chimera_service_set_state(svc->id,CHM_SVC_FAILED);if(svc->critical)return -9;}
 }return 0;
}
extern "C" int chimera_service_stop_all(const chimera_service_manifest*s,uint32_t n,const chimera_service_ops*ops,const chimera_service_plan*p){
 if(!s||!ops||!ops->stop||!p||p->count>n)return -1;int result=0;
 for(uint32_t k=p->count;k>0;--k){const char*id=p->ordered_ids[k-1u];if(find(s,n,id)<0)return -2;if(chimera_service_get_state(id)!=CHM_SVC_RUNNING)continue;
  (void)chimera_service_set_state(id,CHM_SVC_STOPPING);if(ops->stop(id,ops->context)==0)(void)chimera_service_set_state(id,CHM_SVC_STOPPED);else{(void)chimera_service_set_state(id,CHM_SVC_FAILED);result=-3;}
 }return result;
}
extern "C" void chimera_kore_bootstrap(void){/* Service registration is not execution; never fabricate RUNNING state. */}

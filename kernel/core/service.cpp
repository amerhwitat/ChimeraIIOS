#include "../include/chimera/service.h"

namespace {
struct service_state { const char* id; uint32_t state; };
static service_state g_states[64];
static uint32_t g_state_count=0;
static bool same(const char*a,const char*b){
    if(!a||!b)return false;
    while(*a&&*b&&*a==*b){++a;++b;}
    return *a==0&&*b==0;
}
static int find(const chimera_service_manifest*s,uint32_t n,const char*id){
    for(uint32_t i=0;i<n;++i)
        if(same(s[i].id,id))return (int)i;
    return -1;
}
}
extern "C" int chimera_service_validate(const chimera_service_manifest*s,uint32_t n){
    if(!s||!n)return -1;
    for(uint32_t i=0;i<n;++i){
        if(s[i].abi_version!=CHIMERA_SERVICE_ABI||!s[i].id)return -2;
        for(uint32_t j=i+1;j<n;++j)
            if(same(s[i].id,s[j].id))return -3;
        for(uint32_t d=0;d<s[i].dependency_count;++d)
            if(find(s,n,s[i].dependencies[d])<0)return -4;
    }
    return 0;
}
extern "C" int chimera_service_resolve(const chimera_service_manifest*s,uint32_t n,chimera_service_plan*p){
    if(!p||!p->ordered_ids||p->capacity<n)return -1;
    int v=chimera_service_validate(s,n);
    if(v<0)return v;
    uint8_t done[64]={};
    if(n>64)return -5;
    p->count=0;
    while(p->count<n){
        bool progressed=false;
        for(uint32_t i=0;i<n;++i){
            if(done[i])continue;
            bool ready=true;
            for(uint32_t d=0;d<s[i].dependency_count;++d){
                int k=find(s,n,s[i].dependencies[d]);
                if(k<0||!done[(uint32_t)k]){ready=false;break;}
            }
            if(ready){
                done[i]=1;
                p->ordered_ids[p->count++]=s[i].id;
                progressed=true;
            }
        }
        if(!progressed)return -6;
    }
    return 0;
}
extern "C" int chimera_service_set_state(const char*id,uint32_t state){
    if(!id)return -1;
    for(uint32_t i=0;i<g_state_count;++i){
        if(same(g_states[i].id,id)){
            g_states[i].state=state;
            return 0;
        }
    }
    if(g_state_count>=64)return -2;
    g_states[g_state_count++]={id,state};
    return 0;
}
extern "C" uint32_t chimera_service_get_state(const char*id){
    for(uint32_t i=0;i<g_state_count;++i)
        if(same(g_states[i].id,id))return g_states[i].state;
    return CHM_SVC_DECLARED;
}
extern "C" void chimera_kore_bootstrap(void){
    chimera_service_set_state("chimera.device",CHM_SVC_RUNNING);
    chimera_service_set_state("chimera.storage",CHM_SVC_RUNNING);
    chimera_service_set_state("chimera.security",CHM_SVC_RUNNING);
    chimera_service_set_state("chimera.logging",CHM_SVC_RUNNING);
    chimera_service_set_state("chimera.kore",CHM_SVC_RUNNING);
}

#include "chimera/service.h"
#include <cassert>
#include <cstdio>
int main(){
 const char* sd[]={"device"};const char* dd[]={"storage"};
 chimera_service_manifest v[]={
 {CHIMERA_SERVICE_ABI,"device",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,1,0,nullptr},
 {CHIMERA_SERVICE_ABI,"storage",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,1,1,sd},
 {CHIMERA_SERVICE_ABI,"desktop",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,1,1,dd}};
 const char* order[3]={};chimera_service_plan p{0,3,order};
 assert(chimera_service_validate(v,3)==0);assert(chimera_service_resolve(v,3,&p)==0&&p.count==3);
 assert(order[0][0]=='d'&&order[1][0]=='s'&&order[2][0]=='d');
 chimera_service_manifest missing[]={{CHIMERA_SERVICE_ABI,"broken",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,1,nullptr}};
 p.count=123;assert(chimera_service_validate(missing,1)<0);assert(chimera_service_resolve(missing,1,&p)<0&&p.count==0);
 chimera_service_manifest bad[]={{CHIMERA_SERVICE_ABI,"bad",99u,CHM_RESTART_NEVER,1,0,nullptr}};
 assert(chimera_service_validate(bad,1)<0);
 chimera_service_manifest dup[]={{CHIMERA_SERVICE_ABI,"same",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,0,nullptr},{CHIMERA_SERVICE_ABI,"same",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,0,nullptr}};
 assert(chimera_service_validate(dup,2)<0);
 const char*ca[]={"b"};const char*cb[]={"a"};
 chimera_service_manifest cyc[]={{CHIMERA_SERVICE_ABI,"a",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,1,ca},{CHIMERA_SERVICE_ABI,"b",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,1,cb}};
 p.capacity=2;assert(chimera_service_resolve(cyc,2,&p)==-6&&p.count==0);
 assert(chimera_service_set_state("valid",CHM_SVC_RUNNING)==0);assert(chimera_service_set_state("invalid",99u)<0);
 puts("service manifest bounds, dependency validation, cycle rollback and state validation passed");
}

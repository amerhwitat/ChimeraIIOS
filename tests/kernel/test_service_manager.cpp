#include <assert.h>
#include <string.h>
#include "chimera/service.h"

struct context { const char* fail_start; const char* fail_health; unsigned starts; unsigned health_checks; };
static int start_service(const chimera_service_manifest* s, void* p) {
    context* c=(context*)p; ++c->starts;
    return c->fail_start && strcmp(c->fail_start,s->id)==0 ? -1 : 0;
}
static int health_service(const chimera_service_manifest* s, void* p) {
    context* c=(context*)p; ++c->health_checks;
    return c->fail_health && strcmp(c->fail_health,s->id)==0 ? -1 : 0;
}
static const char* d_device[]={"device"};
static const char* d_network[]={"optional-network"};
static const char* d_desktop[]={"graphics","storage"};
static const char* d_cycle_a[]={"cycle-b"};
static const char* d_cycle_b[]={"cycle-a"};
int main() {
    {
        chimera_service_manifest s[]={
          {CHIMERA_SERVICE_ABI,"device",0,CHM_RESTART_NEVER,1,0,0},
          {CHIMERA_SERVICE_ABI,"storage",0,CHM_RESTART_NEVER,1,1,d_device},
          {CHIMERA_SERVICE_ABI,"graphics",0,CHM_RESTART_NEVER,0,1,d_device},
          {CHIMERA_SERVICE_ABI,"desktop",0,CHM_RESTART_NEVER,0,2,d_desktop}
        };
        context c={0,0,0,0}; chimera_service_ops ops={start_service,health_service};
        chimera_service_report r={};
        assert(chimera_service_start_graph(s,4,&ops,&c,&r)==0);
        assert(r.ready==4 && r.failed==0 && r.blocked==0);
        assert(c.starts==4 && c.health_checks==4);
        assert(chimera_service_get_state("desktop")==CHM_SVC_RUNNING);
    }
    {
        chimera_service_manifest s[]={
          {CHIMERA_SERVICE_ABI,"optional-network",0,CHM_RESTART_NEVER,0,0,0},
          {CHIMERA_SERVICE_ABI,"network-app",0,CHM_RESTART_NEVER,0,1,d_network},
          {CHIMERA_SERVICE_ABI,"independent",0,CHM_RESTART_NEVER,0,0,0}
        };
        context c={"optional-network",0,0,0}; chimera_service_ops ops={start_service,health_service};
        chimera_service_report r={};
        assert(chimera_service_start_graph(s,3,&ops,&c,&r)==0);
        assert(r.failed==1 && r.blocked==1 && r.ready==1);
        assert(chimera_service_get_state("network-app")==CHM_SVC_BLOCKED);
        assert(chimera_service_get_state("independent")==CHM_SVC_RUNNING);
    }
    {
        chimera_service_manifest s[]={
          {CHIMERA_SERVICE_ABI,"critical-failure",0,CHM_RESTART_NEVER,1,0,0}
        };
        context c={0,"critical-failure",0,0}; chimera_service_ops ops={start_service,health_service};
        chimera_service_report r={};
        assert(chimera_service_start_graph(s,1,&ops,&c,&r)==-13);
        assert(chimera_service_get_state("critical-failure")==CHM_SVC_FAILED);
    }
    {
        chimera_service_manifest s[]={
          {CHIMERA_SERVICE_ABI,"cycle-a",0,CHM_RESTART_NEVER,0,1,d_cycle_a},
          {CHIMERA_SERVICE_ABI,"cycle-b",0,CHM_RESTART_NEVER,0,1,d_cycle_b}
        };
        const char* ids[2]; chimera_service_plan p={0,2,ids};
        assert(chimera_service_resolve(s,2,&p)==-6);
    }
    {
        chimera_service_manifest s[]={
          {CHIMERA_SERVICE_ABI,"no-callbacks",0,CHM_RESTART_NEVER,0,0,0}
        };
        chimera_service_report r={};
        assert(chimera_service_start_graph(s,1,0,0,&r)==-8);
    }
    return 0;
}

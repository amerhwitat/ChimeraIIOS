#include "chimera/service.h"
#include <stdio.h>
#include <string.h>

namespace {
struct fake_service { const char* id; uint64_t handle; int starts; int stops; int probes; int exit_code; bool alive; bool healthy; };
fake_service g_fake[4] = {};
uint32_t g_count = 0;
void reset() { memset(g_fake, 0, sizeof(g_fake)); g_count = 0; }
fake_service* find_fake(const char* id) {
    for (uint32_t i=0;i<g_count;++i) if (strcmp(g_fake[i].id,id)==0) return &g_fake[i];
    return nullptr;
}
int start_cb(const char* id, uint64_t* handle, void*) {
    fake_service* s=find_fake(id); if (!s || !handle) return -1;
    ++s->starts; s->alive=true; s->healthy=true; s->handle=static_cast<uint64_t>(s->starts);
    *handle=s->handle; return 0;
}
int probe_cb(const char* id, uint64_t handle, void*) {
    fake_service* s=find_fake(id); if (!s || !s->alive || s->handle!=handle) return -1;
    ++s->probes; return s->healthy ? 1 : 0;
}
int wait_cb(const char* id, uint64_t handle, int* code, void*) {
    fake_service* s=find_fake(id); if (!s || !code || s->handle!=handle) return -1;
    if (s->alive) return 0;
    *code=s->exit_code; return 1;
}
int stop_cb(const char* id, uint64_t handle, void*) {
    fake_service* s=find_fake(id); if (!s || s->handle!=handle) return -1;
    ++s->stops; s->alive=false; return 0;
}
void sleep_cb(uint32_t, void*) {}
void add_fake(const char* id) { g_fake[g_count++]={id,0,0,0,0,0,false,false}; }
}

int main() {
    reset();
    add_fake("storage"); add_fake("device"); add_fake("aurora");
    const char* device_deps[]={"storage"};
    const char* aurora_deps[]={"device"};
    const chimera_service_manifest services[] = {
      {CHIMERA_SERVICE_ABI,"aurora",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,1,1,aurora_deps},
      {CHIMERA_SERVICE_ABI,"device",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,1,1,device_deps},
      {CHIMERA_SERVICE_ABI,"storage",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,0,nullptr}
    };
    chimera_service_backend backend={start_cb,probe_cb,wait_cb,stop_cb,sleep_cb,nullptr};
    chimera_service_supervisor_config config={2,1,1,1};
    if (chimera_service_supervisor_start(services,3,&backend,&config)!=0) {
      fprintf(stderr,"FAIL: dependency-ordered start failed\n"); return 1;
    }
    if (chimera_service_get_state("storage")!=CHM_SVC_RUNNING ||
        chimera_service_get_state("device")!=CHM_SVC_RUNNING ||
        chimera_service_get_state("aurora")!=CHM_SVC_RUNNING) {
      fprintf(stderr,"FAIL: services not health-confirmed\n"); return 2;
    }
    /* A process exit is detected by wait_exit and restarted only within policy. */
    fake_service* aurora=find_fake("aurora");
    aurora->alive=false; aurora->exit_code=17;
    if (chimera_service_supervisor_poll()!=0 || aurora->starts!=2 ||
        chimera_service_get_state("aurora")!=CHM_SVC_RUNNING) {
      fprintf(stderr,"FAIL: bounded restart/health confirmation failed\n"); return 3;
    }
    if (chimera_service_supervisor_stop()!=0 ||
        chimera_service_get_state("aurora")!=CHM_SVC_STOPPED ||
        chimera_service_get_state("device")!=CHM_SVC_STOPPED ||
        chimera_service_get_state("storage")!=CHM_SVC_STOPPED) {
      fprintf(stderr,"FAIL: reverse-order stop failed\n"); return 4;
    }
    /* A dependency exit must stop dependent services instead of leaving them
       falsely RUNNING against a dead prerequisite. */
    reset();
    add_fake("storage"); add_fake("device"); add_fake("aurora");
    if (chimera_service_supervisor_start(services,3,&backend,&config)!=0) {
      fprintf(stderr,"FAIL: second supervisor start failed\\n"); return 5;
    }
    fake_service* storage=find_fake("storage");
    storage->alive=false; storage->exit_code=9;
    if (chimera_service_supervisor_poll()!=-2 ||
        chimera_service_get_state("storage")!=CHM_SVC_FAILED ||
        chimera_service_get_state("device")!=CHM_SVC_BLOCKED ||
        chimera_service_get_state("aurora")!=CHM_SVC_BLOCKED ||
        find_fake("device")->alive || find_fake("aurora")->alive) {
      fprintf(stderr,"FAIL: dependency failure did not cascade-stop dependents\\n"); return 6;
    }
    if (chimera_service_supervisor_stop()!=0) {
      fprintf(stderr,"FAIL: cleanup after dependency cascade failed\\n"); return 7;
    }
    puts("PASS: dependency order, health probes, exit monitoring, bounded restart, reverse stop and dependency-failure cascade");
    return 0;
}

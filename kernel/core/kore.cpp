#include "chimera/kore.h"
#include "chimera/scheduler.h"
#include <stddef.h>
#include <stdint.h>

namespace {
constexpr uint32_t MAX_UNITS = 64;
constexpr uint32_t MAX_EDGES = 128;
struct Edge { uint32_t from; uint32_t to; };
static kore_unit_info units[MAX_UNITS];
static Edge wants[MAX_EDGES], requires_[MAX_EDGES], afters[MAX_EDGES];
static uint32_t unit_count = 0, wants_count = 0, requires_count = 0, after_count = 0;
static uint32_t kore_cpus = 1;

static void clear_unit(kore_unit_info &u) { u = {}; u.state = KORE_DEAD; }
static int find_unit(const char *name) {
    if (!name) return -1;
    for (uint32_t i=0;i<unit_count;i++) {
        const char *a=units[i].name; const char *b=name; if (!a) continue;
        while (*a && *b && *a==*b) { ++a; ++b; }
        if (!*a && !*b) return (int)i;
    }
    return -1;
}
static bool edge_exists(const Edge *e, uint32_t n, uint32_t from, uint32_t to) {
    for (uint32_t i=0;i<n;i++) if (e[i].from==from && e[i].to==to) return true;
    return false;
}
static bool has_path(const Edge *e, uint32_t n, uint32_t from, uint32_t to, uint32_t depth=0) {
    if (from==to) return true;
    if (depth>MAX_UNITS) return false;
    for (uint32_t i=0;i<n;i++) if (e[i].from==from && has_path(e,n,e[i].to,to,depth+1)) return true;
    return false;
}
static void service_task(void *arg) {
    uint32_t id=(uint32_t)(uintptr_t)arg;
    if (id>=unit_count) return;
    units[id].state=KORE_STARTING;
    if (units[id].start) units[id].start(units[id].arg);
    units[id].runs++;
    units[id].state=KORE_RUNNING;
}
static bool dependency_ready(uint32_t id) {
    for (uint32_t i=0;i<requires_count;i++) if (requires_[i].from==id && units[requires_[i].to].state!=KORE_RUNNING) return false;
    for (uint32_t i=0;i<after_count;i++) if (afters[i].from==id && units[afters[i].to].state!=KORE_RUNNING && units[afters[i].to].state!=KORE_STOPPED) return false;
    return true;
}
}

extern "C" void kore_init(uint32_t cpu_count) {
    kore_cpus=cpu_count?cpu_count:1; unit_count=wants_count=requires_count=after_count=0;
    for (uint32_t i=0;i<MAX_UNITS;i++) clear_unit(units[i]);
}
extern "C" int kore_register_service(const char *name,kore_service_fn fn,void *arg,uint32_t priority) {
    if (!name || unit_count>=MAX_UNITS || find_unit(name)>=0) return -1;
    auto &u=units[unit_count]; clear_unit(u); u.id=unit_count; u.type=KORE_UNIT_SERVICE; u.name=name; u.start=fn; u.arg=arg; u.priority=priority; return (int)unit_count++;
}
extern "C" int kore_register_target(const char *name,uint32_t priority) {
    if (!name || unit_count>=MAX_UNITS || find_unit(name)>=0) return -1;
    auto &u=units[unit_count]; clear_unit(u); u.id=unit_count; u.type=KORE_UNIT_TARGET; u.name=name; u.priority=priority; return (int)unit_count++;
}
extern "C" int kore_add_wants(const char *target,const char *unit) {
    int a=find_unit(target),b=find_unit(unit); if(a<0||b<0||wants_count>=MAX_EDGES) return -1;
    if(!edge_exists(wants,wants_count,(uint32_t)a,(uint32_t)b)) wants[wants_count++]={(uint32_t)a,(uint32_t)b}; units[a].wanted_by++; return 0;
}
extern "C" int kore_add_requires(const char *unit,const char *required) {
    int a=find_unit(unit),b=find_unit(required); if(a<0||b<0||requires_count>=MAX_EDGES) return -1;
    if(a==b || has_path(requires,requires_count,(uint32_t)b,(uint32_t)a)) return -2;
    if(!edge_exists(requires,requires_count,(uint32_t)a,(uint32_t)b)) requires_[requires_count++]={(uint32_t)a,(uint32_t)b}; units[a].requires_count++; return 0;
}
extern "C" int kore_add_after(const char *unit,const char *after) {
    int a=find_unit(unit),b=find_unit(after); if(a<0||b<0||after_count>=MAX_EDGES) return -1;
    if(a==b) return -2;
    if(!edge_exists(afters,after_count,(uint32_t)a,(uint32_t)b)) afters[after_count++]={(uint32_t)a,(uint32_t)b}; units[a].after_count++; return 0;
}
extern "C" int kore_start_target(const char *target) {
    int t=find_unit(target); if(t<0 || units[t].type!=KORE_UNIT_TARGET) return -1;
    units[t].state=KORE_STARTING;
    for(uint32_t i=0;i<wants_count;i++) if(wants[i].from==(uint32_t)t && units[wants[i].to].state==KORE_DEAD) units[wants[i].to].state=KORE_QUEUED;
    units[t].state=KORE_RUNNING;
    return 0;
}
extern "C" uint32_t kore_dispatch(uint32_t budget) {
    uint32_t started=0; if(!budget) budget=unit_count;
    for(uint32_t pass=0;pass<MAX_UNITS && started<budget;pass++) {
        bool progress=false;
        for(uint32_t i=0;i<unit_count && started<budget;i++) {
            if(units[i].type!=KORE_UNIT_SERVICE || units[i].state!=KORE_QUEUED || !dependency_ready(i)) continue;
            int tid=chimera_sched_submit(service_task,(void*)(uintptr_t)i,units[i].priority);
            if(tid<0) { units[i].state=KORE_FAILED; units[i].last_error=1; continue; }
            units[i].state=KORE_RUNNING; started++; progress=true;
        }
        if(!progress) break;
    }
    return started;
}
extern "C" uint32_t kore_running_count(void) { uint32_t n=0; for(uint32_t i=0;i<unit_count;i++) if(units[i].state==KORE_RUNNING) n++; return n; }
extern "C" uint32_t kore_failed_count(void) { uint32_t n=0; for(uint32_t i=0;i<unit_count;i++) if(units[i].state==KORE_FAILED) n++; return n; }
extern "C" uint32_t kore_unit_count(void) { return unit_count; }
extern "C" const kore_unit_info *kore_snapshot(uint32_t index) { return index<unit_count ? &units[index] : nullptr; }
extern "C" void kore_print_status(void) { (void)kore_cpus; }

/*
 * Koronos CPU Manager
 * Detects CPU topology and manages parallel execution
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/sysinfo.h>
#include <pthread.h>

typedef struct {
    int cpu_id;
    int online;
    long freq_mhz;
    int siblings;
} cpu_core_t;

typedef struct {
    int total_cpus;
    int online_cpus;
    long total_mem;
    long free_mem;
    cpu_core_t *cores;
} cpu_topology_t;

static cpu_topology_t *global_topo = NULL;
static pthread_mutex_t cpu_lock = PTHREAD_MUTEX_INITIALIZER;

cpu_topology_t* cpu_detect_topology(void) {
    pthread_mutex_lock(&cpu_lock);
    
    cpu_topology_t *topo = malloc(sizeof(cpu_topology_t));
    if (!topo) return NULL;
    
    // Detect number of CPUs
    topo->total_cpus = sysconf(_SC_NPROCESSORS_CONF);
    topo->online_cpus = sysconf(_SC_NPROCESSORS_ONLN);
    
    // Get memory info
    struct sysinfo si;
    sysinfo(&si);
    topo->total_mem = si.totalram * si.mem_unit;
    topo->free_mem = si.freeram * si.mem_unit;
    
    // Allocate core array
    topo->cores = malloc(sizeof(cpu_core_t) * topo->total_cpus);
    for (int i = 0; i < topo->total_cpus; i++) {
        topo->cores[i].cpu_id = i;
        topo->cores[i].online = (i < topo->online_cpus) ? 1 : 0;
    }
    
    global_topo = topo;
    pthread_mutex_unlock(&cpu_lock);
    return topo;
}

int cpu_get_count(void) {
    if (!global_topo) cpu_detect_topology();
    return global_topo ? global_topo->online_cpus : 1;
}

int cpu_get_optimal_threads(void) {
    // Limit to prevent oversubscription
    int online = cpu_get_count();
    return (online > 4) ? online - 1 : online;
}

void cpu_print_topology(void) {
    if (!global_topo) cpu_detect_topology();
    if (!global_topo) return;
    
    printf("\n[CPU TOPOLOGY]\n");
    printf("  Total CPUs configured: %d\n", global_topo->total_cpus);
    printf("  Online CPUs: %d\n", global_topo->online_cpus);
    printf("  Total memory: %ld MB\n", global_topo->total_mem / (1024 * 1024));
    printf("  Free memory: %ld MB\n", global_topo->free_mem / (1024 * 1024));
    printf("  Optimal parallel threads: %d\n", cpu_get_optimal_threads());
    printf("\n");
}

void cpu_free_topology(cpu_topology_t *topo) {
    if (topo) {
        free(topo->cores);
        free(topo);
    }
}

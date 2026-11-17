/*
 * Koronos Service Manager
 * Manages parallel startup of system services
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <pthread.h>
#include <string.h>

#define MAX_SERVICES 32

typedef struct {
    const char *name;
    const char *binary;
    int priority;
    int depends_on;
    int running;
    pid_t pid;
} service_t;

typedef struct {
    service_t services[MAX_SERVICES];
    int count;
    int max_parallel;
    pthread_mutex_t lock;
} service_manager_t;

static service_manager_t manager;

void service_manager_init(int max_parallel_services) {
    memset(&manager, 0, sizeof(manager));
    pthread_mutex_init(&manager.lock, NULL);
    manager.max_parallel = max_parallel_services;
    printf("[SERVICE_MANAGER] Initialized with max %d parallel services\n", max_parallel_services);
}

int service_register(const char *name, const char *binary, int priority) {
    pthread_mutex_lock(&manager.lock);
    
    if (manager.count >= MAX_SERVICES) {
        pthread_mutex_unlock(&manager.lock);
        return -1;
    }
    
    service_t *svc = &manager.services[manager.count];
    svc->name = strdup(name);
    svc->binary = strdup(binary);
    svc->priority = priority;
    svc->running = 0;
    svc->pid = 0;
    manager.count++;
    
    printf("[SERVICE_MANAGER] Registered: %s (priority %d)\n", name, priority);
    pthread_mutex_unlock(&manager.lock);
    return manager.count - 1;
}

int service_start_parallel(void) {
    printf("[SERVICE_MANAGER] Starting services in parallel (max %d concurrent)...\n", manager.max_parallel);
    
    int running = 0;
    int started = 0;
    
    while (started < manager.count || running > 0) {
        // Start new services if under max parallel limit
        for (int i = 0; i < manager.count && running < manager.max_parallel; i++) {
            service_t *svc = &manager.services[i];
            if (!svc->running && svc->pid == 0) {
                pid_t pid = fork();
                if (pid == 0) {
                    // Child process
                    execl(svc->binary, svc->binary, NULL);
                    exit(1);
                } else {
                    // Parent tracking
                    svc->pid = pid;
                    svc->running = 1;
                    running++;
                    started++;
                    printf("[SERVICE_MANAGER] Started: %s (PID %d)\n", svc->name, pid);
                }
            }
        }
        
        // Wait for any service to complete
        if (running > 0) {
            pid_t finished = wait(NULL);
            for (int i = 0; i < manager.count; i++) {
                if (manager.services[i].pid == finished) {
                    manager.services[i].running = 0;
                    running--;
                    printf("[SERVICE_MANAGER] Finished: %s (PID %d)\n", 
                           manager.services[i].name, finished);
                    break;
                }
            }
        }
    }
    
    printf("[SERVICE_MANAGER] All %d services started\n", manager.count);
    return 0;
}

void service_manager_cleanup(void) {
    pthread_mutex_destroy(&manager.lock);
    for (int i = 0; i < manager.count; i++) {
        if (manager.services[i].name) free((void *)manager.services[i].name);
        if (manager.services[i].binary) free((void *)manager.services[i].binary);
    }
}

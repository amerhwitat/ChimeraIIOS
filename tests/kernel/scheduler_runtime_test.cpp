#include "chimera/scheduler.h"
#include <assert.h>
#include <stdio.h>
static int trace[16],trace_count,blocker_runs; static uint32_t blocked_id;
static void high_task(void*){trace[trace_count++]=2;}
static void low_task(void*){trace[trace_count++]=1;}
static void blocker_task(void*){++blocker_runs;if(blocker_runs==1)chimera_sched_block();}
int main(){
    chimera_sched_init(1);
    int low=chimera_sched_submit(low_task,nullptr,10);
    int high=chimera_sched_submit(high_task,nullptr,100);
    assert(low>0&&high>0);
    assert(chimera_sched_run_once(0)==1);
    assert(trace_count==1&&trace[0]==2);
    assert(chimera_sched_run_once(0)==1);
    assert(trace_count==2&&trace[1]==2);
    chimera_sched_init(1); trace_count=0; blocker_runs=0;
    blocked_id=(uint32_t)chimera_sched_submit(blocker_task,nullptr,50);
    assert(blocked_id>0);
    assert(chimera_sched_run_once(0)==1&&blocker_runs==1);
    assert(chimera_sched_runnable_count()==0);
    chimera_sched_wake(blocked_id);
    assert(chimera_sched_runnable_count()==1);
    assert(chimera_sched_run_once(0)==1&&blocker_runs==2);
    chimera_task_info info[8]={}; uint32_t n=chimera_sched_snapshot(info,8);
    assert(n==1&&info[0].id==blocked_id&&info[0].runs==2);
    puts("Koronos scheduler runtime: PASS"); return 0;
}

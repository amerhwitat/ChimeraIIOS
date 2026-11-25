#include "chimera/scheduler.h"
#include <assert.h>
#include <stdio.h>
static int trace[16],trace_count,blocker_runs; static uint32_t blocked_id,high_runs; static int fair_runs[3];
static void high_task(void*){trace[trace_count++]=2;++high_runs;if(high_runs==1)chimera_sched_block();}
static void low_task(void*){trace[trace_count++]=1;}
static void blocker_task(void*){++blocker_runs;if(blocker_runs==1)chimera_sched_block();}
static void fair_high(void*){++fair_runs[0];}
static void fair_mid(void*){++fair_runs[1];}
static void fair_low(void*){++fair_runs[2];}
static int reentrant_runs=0,reentrant_nested_runs=0;
static void reentrant_task(void*){++reentrant_runs;reentrant_nested_runs+=(int)chimera_sched_run_once(0);}
static int exit_after_block_runs=0;
static void exit_after_block_task(void*){++exit_after_block_runs;chimera_sched_block();chimera_sched_exit();}
int main(){
    chimera_sched_init(1);
    int low=chimera_sched_submit(low_task,nullptr,10);
    int high=chimera_sched_submit(high_task,nullptr,100);
    assert(low>0&&high>0);
    assert(chimera_sched_run_once(0)==1);
    assert(trace_count==1&&trace[0]==2);
    assert(chimera_sched_runnable_count()==1);
    assert(chimera_sched_run_once(0)==1);
    assert(trace_count==2&&trace[1]==1);
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

    // Regression test for the ISO monitor starvation seen on real VGA output:
    // a permanently READY high-priority task must not prevent lower-priority
    // READY tasks from receiving dispatches.
    chimera_sched_init(1); fair_runs[0]=fair_runs[1]=fair_runs[2]=0;
    assert(chimera_sched_submit(fair_high,nullptr,110)>0);
    assert(chimera_sched_submit(fair_mid,nullptr,90)>0);
    assert(chimera_sched_submit(fair_low,nullptr,80)>0);
    for(int i=0;i<6;i++) assert(chimera_sched_run_once(0)==1);
    assert(fair_runs[0]>=2&&fair_runs[1]>=2&&fair_runs[2]>=2);

    // Affinity masks must refer only to configured logical CPUs. Invalid
    // masks used to be accepted and silently stranded tasks forever.
    chimera_sched_init(1);
    int affinity_runs = 0;
    int affinity_task = chimera_sched_submit([](void *arg) { ++*static_cast<int *>(arg); }, &affinity_runs, 10);
    assert(affinity_task > 0);
    assert(chimera_sched_set_affinity((uint32_t)affinity_task, 2ull) == -3);
    assert(chimera_sched_set_affinity((uint32_t)affinity_task, 1ull) == 0);
    assert(chimera_sched_run_once(0) == 1 && affinity_runs == 1);

    chimera_sched_init(2);
    affinity_runs = 0;
    affinity_task = chimera_sched_submit([](void *arg) { ++*static_cast<int *>(arg); }, &affinity_runs, 10);
    assert(affinity_task > 0);
    assert(chimera_sched_set_affinity((uint32_t)affinity_task, 4ull) == -3);
    assert(chimera_sched_set_affinity((uint32_t)affinity_task, 2ull) == 0);
    assert(chimera_sched_run_once(0) == 0 && affinity_runs == 0);
    assert(chimera_sched_run_once(1) == 1 && affinity_runs == 1);

    chimera_sched_init(2);
    int serial_runs = 0;
    auto serial_task = [](void *arg) { ++*static_cast<int *>(arg); };
    assert(chimera_sched_submit(serial_task,&serial_runs,10)>0);
    assert(chimera_sched_submit(serial_task,&serial_runs,10)>0);
    assert(chimera_sched_run_parallel(0,2)==0 && serial_runs==0);
    assert(chimera_sched_run_serial_range(0,2)==2 && serial_runs==2);

    // A callback must retain ownership of its CPU until it returns. A nested
    // run_once on that CPU must not overwrite current_index or dispatch a
    // second callback on the same execution stack.
    chimera_sched_init(1); reentrant_runs=0; reentrant_nested_runs=0;
    assert(chimera_sched_submit(reentrant_task,nullptr,10)>0);
    assert(chimera_sched_run_once(0)==1);
    assert(reentrant_runs==1 && reentrant_nested_runs==0);
    assert(chimera_sched_run_once(0)==1);
    assert(reentrant_runs==2 && reentrant_nested_runs==0);
    // EXIT is terminal and must supersede an earlier BLOCK request made
    // during the same callback. A subsequent wake must not revive the task.
    chimera_sched_init(1); exit_after_block_runs=0;
    int exit_after_block_id=chimera_sched_submit(exit_after_block_task,nullptr,10);
    assert(exit_after_block_id>0);
    assert(chimera_sched_run_once(0)==1 && exit_after_block_runs==1);
    n=chimera_sched_snapshot(info,8);
    assert(n==1 && info[0].id==(uint32_t)exit_after_block_id);
    assert(info[0].state==CHIMERA_TASK_EXITED);
    chimera_sched_wake((uint32_t)exit_after_block_id);
    assert(chimera_sched_runnable_count()==0);
    assert(chimera_sched_run_once(0)==0);

    puts("Koronos scheduler runtime: PASS"); return 0;
}

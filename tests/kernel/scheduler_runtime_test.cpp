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
static int affinity_runs,serial_runs;
static void serial_task(void*){++serial_runs;}
static void affinity_task(void*){++affinity_runs;}
static int reentrant_outer_runs,reentrant_inner_runs;
static uint32_t reentrant_nested_result;
static void reentrant_inner(void*) { ++reentrant_inner_runs; }
static void reentrant_outer(void*) {
    ++reentrant_outer_runs;
    /* A nested dispatch on the same CPU must not overwrite the active owner. */
    reentrant_nested_result=chimera_sched_run_once(0);
}
static int boundary_runs;
static void boundary_block(void*) {
    ++boundary_runs;
    assert(chimera_sched_block_on_cpu(0)==0);
    /* The block is deferred: the callback continues under exclusive ownership. */
    chimera_task_info info[4]={}; assert(chimera_sched_snapshot(info,4)==1);
    assert(info[0].state==CHIMERA_TASK_RUNNING);
}
static void boundary_exit(void*) { ++boundary_runs; assert(chimera_sched_exit_on_cpu(0)==0); }
static void wrong_cpu_action(void*) { ++boundary_runs; assert(chimera_sched_block_on_cpu(1)==-1); }
int main(){
    chimera_sched_init(1);
    int low=chimera_sched_submit(low_task,nullptr,10),high=chimera_sched_submit(high_task,nullptr,100);
    assert(low>0&&high>0&&chimera_sched_run_once(0)==1);
    assert(trace_count==1&&trace[0]==2&&chimera_sched_runnable_count()==1);
    assert(chimera_sched_run_once(0)==1&&trace_count==2&&trace[1]==1);
    chimera_sched_init(1);trace_count=0;blocker_runs=0;
    blocked_id=(uint32_t)chimera_sched_submit(blocker_task,nullptr,50);
    assert(blocked_id>0&&chimera_sched_run_once(0)==1&&blocker_runs==1);
    assert(chimera_sched_runnable_count()==0);chimera_sched_wake(blocked_id);
    assert(chimera_sched_runnable_count()==1&&chimera_sched_run_once(0)==1&&blocker_runs==2);
    chimera_task_info info[8]={};uint32_t n=chimera_sched_snapshot(info,8);
    assert(n==1&&info[0].id==blocked_id&&info[0].runs==2);

    chimera_sched_init(1);fair_runs[0]=fair_runs[1]=fair_runs[2]=0;
    assert(chimera_sched_submit(fair_high,nullptr,110)>0);
    assert(chimera_sched_submit(fair_mid,nullptr,90)>0);
    assert(chimera_sched_submit(fair_low,nullptr,80)>0);
    for(int i=0;i<6;i++)assert(chimera_sched_run_once(0)==1);
    assert(fair_runs[0]>=2&&fair_runs[1]>=2&&fair_runs[2]>=2);

    chimera_sched_init(2);serial_runs=0;
    assert(chimera_sched_submit(serial_task,nullptr,10)>0);
    assert(chimera_sched_submit(serial_task,nullptr,10)>0);
    /* The old run_parallel implementation was just a serial for-loop. */
    assert(chimera_sched_run_parallel(0,2)==0&&serial_runs==0);
    assert(chimera_sched_run_serial_range(0,2)==2&&serial_runs==2);

    chimera_sched_init(65);affinity_runs=0;
    int cpu0=chimera_sched_submit(affinity_task,nullptr,10);
    assert(cpu0>0&&chimera_sched_set_affinity((uint32_t)cpu0,1ull)==0);
    assert(chimera_sched_run_once(64)==0&&affinity_runs==0);
    assert(chimera_sched_run_once(0)==1&&affinity_runs==1);
    chimera_sched_init(65);affinity_runs=0;
    int cpu63=chimera_sched_submit(affinity_task,nullptr,10);
    assert(cpu63>0&&chimera_sched_set_affinity((uint32_t)cpu63,1ull<<63)==0);
    assert(chimera_sched_run_once(0)==0&&chimera_sched_run_once(64)==0&&affinity_runs==0);
    assert(chimera_sched_run_once(63)==1&&affinity_runs==1);
    chimera_sched_init(65);affinity_runs=0;
    assert(chimera_sched_submit(affinity_task,nullptr,10)>0);
    assert(chimera_sched_run_once(64)==1&&affinity_runs==1);

    chimera_sched_init(1);reentrant_outer_runs=reentrant_inner_runs=0;reentrant_nested_result=99;
    int inner=chimera_sched_submit(reentrant_inner,nullptr,10);
    int outer=chimera_sched_submit(reentrant_outer,nullptr,100);
    assert(inner>0&&outer>0);
    assert(chimera_sched_run_once(0)==1);
    assert(reentrant_outer_runs==1&&reentrant_inner_runs==0&&reentrant_nested_result==0);
    assert(chimera_sched_run_once(0)==1&&reentrant_inner_runs==1);

    chimera_sched_init(1);boundary_runs=0;
    int b=chimera_sched_submit(boundary_block,nullptr,10);
    assert(b>0&&chimera_sched_run_once(0)==1&&boundary_runs==1);
    assert(chimera_sched_snapshot(info,8)==1&&info[0].state==CHIMERA_TASK_BLOCKED);
    chimera_sched_init(1);boundary_runs=0;
    int e=chimera_sched_submit(boundary_exit,nullptr,10);
    assert(e>0&&chimera_sched_run_once(0)==1);
    assert(chimera_sched_snapshot(info,8)==1&&info[0].state==CHIMERA_TASK_EXITED);
    chimera_sched_init(1);boundary_runs=0;
    assert(chimera_sched_submit(wrong_cpu_action,nullptr,10)>0);
    assert(chimera_sched_run_once(0)==1);
    assert(chimera_sched_snapshot(info,8)==1&&info[0].state==CHIMERA_TASK_READY);
    puts("Koronos scheduler runtime: PASS");return 0;
}

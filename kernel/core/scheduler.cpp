#include "chimera/scheduler.h"
namespace { constexpr uint32_t MAX_CPUS=256,MAX_TASKS=1024; struct Task{chimera_task_fn fn;void* arg;chimera_task_info info;}; Task tasks[MAX_TASKS]; volatile uint32_t count=0,next_id=1,rr=0,cpus=1,lock_word=0;
static void lock(){while(__sync_lock_test_and_set(&lock_word,1u)){} } static void unlock(){__sync_lock_release(&lock_word);}
}
extern "C" void chimera_sched_init(uint32_t n){cpus=n?n:1;if(cpus>MAX_CPUS)cpus=MAX_CPUS;lock();count=0;rr=0;for(uint32_t i=0;i<MAX_TASKS;i++)tasks[i]={};unlock();}
extern "C" uint32_t chimera_sched_cpu_count(){return cpus;}
extern "C" int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority){if(!fn)return -1;lock();if(count>=MAX_TASKS){unlock();return -2;}uint32_t i=count++;tasks[i].fn=fn;tasks[i].arg=arg;tasks[i].info={next_id++,0,0,priority,0,0};int id=(int)tasks[i].info.id;unlock();return id;}
extern "C" uint32_t chimera_sched_run_once(uint32_t cpu){uint32_t ran=0;lock();uint32_t n=count,start=rr++;unlock();for(uint32_t k=0;k<n;k++){uint32_t i=(start+k)%n;lock();if(tasks[i].info.state!=0){unlock();continue;}tasks[i].info.state=1;tasks[i].info.cpu=cpu;chimera_task_fn f=tasks[i].fn;void* a=tasks[i].arg;unlock();f(a);lock();tasks[i].info.runs++;tasks[i].info.ticks++;tasks[i].info.state=2;unlock();ran++;}return ran;}
extern "C" uint32_t chimera_sched_snapshot(chimera_task_info* out,uint32_t cap){if(!out)return 0;lock();uint32_t n=count<cap?count:cap;for(uint32_t i=0;i<n;i++)out[i]=tasks[i].info;unlock();return n;}
#include "chimera.h"
#include <stdio.h>
#include <string.h>
static int failures=0;
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL: %s:%d: %s\n",__FILE__,__LINE__,#x);failures++;}}while(0)
static void test_init_step_reset(void){ChimeraState s;CHECK(chimera_init(&s,2,4)==0);CHECK(s.cpu_count==2);CHECK(s.brain.node_count==4);CHECK(s.run_state==CHIMERA_PAUSED);CHECK(s.cpus[0].regs[0].bytes[0]==0);CHECK(chimera_step(&s)==0);CHECK(s.ticks==1);CHECK(s.cpus[0].instructions==1);CHECK(s.cpus[0].pc==4);CHECK(s.messages_sent==1);CHECK(s.messages_delivered==1);chimera_reset(&s);CHECK(s.ticks==0);CHECK(s.cpus[0].instructions==0);chimera_destroy(&s);}
static void test_scheduler_rotation(void){ChimeraState s;CHECK(chimera_init(&s,3,6)==0);chimera_step(&s);chimera_step(&s);chimera_step(&s);chimera_step(&s);CHECK(s.cpus[0].instructions==2);CHECK(s.cpus[1].instructions==1);CHECK(s.cpus[2].instructions==1);CHECK(s.brain.edge_count>=6);CHECK(s.brain.edges[0].packets>0);chimera_destroy(&s);}
static void test_control_json(void){ChimeraState s;char json[CHIMERA_JSON_MAX];CHECK(chimera_init(&s,1,3)==0);CHECK(chimera_control(&s,"start")==0);CHECK(s.run_state==CHIMERA_RUNNING);CHECK(chimera_control(&s,"pause")==0);CHECK(s.run_state==CHIMERA_PAUSED);CHECK(chimera_control(&s,"wat")!=0);CHECK(chimera_state_json(&s,json,sizeof json)>0);CHECK(strstr(json,"\"cpus\"")!=NULL);CHECK(strstr(json,"\"brain\"")!=NULL);chimera_destroy(&s);}
int main(void){test_init_step_reset();test_control_json();test_scheduler_rotation();if(failures)return 1;puts("chimera tests: PASS");return 0;}

#define _POSIX_C_SOURCE 200809L
#include "chimera.h"
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>
#define PORT 8080
#define REQ_MAX 8192
static volatile sig_atomic_t keep_running=1; static ChimeraState sim; static pthread_t sim_thread; static const char*web_root="web";
static void on_sigint(int sig){(void)sig;keep_running=0;}
static void*simulation_loop(void*unused){(void)unused;while(keep_running){pthread_mutex_lock(&sim.lock);int running=(sim.run_state==CHIMERA_RUNNING);pthread_mutex_unlock(&sim.lock);if(running)chimera_step(&sim);struct timespec ts={0,50000000L};nanosleep(&ts,NULL);}return NULL;}
static void send_text(int fd,int code,const char*type,const char*body){const char*reason=code==200?"OK":(code==400?"Bad Request":(code==404?"Not Found":"Internal Server Error"));dprintf(fd,"HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %zu\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n%s",code,reason,type,strlen(body),body);}
static int safe_static_path(const char*path,char*out,size_t cap){if(strstr(path,"..")||strchr(path,'\\'))return-1;if(strcmp(path,"/")==0)path="/index.html";int n=snprintf(out,cap,"%s%s",web_root,path);return n>0&&(size_t)n<cap?0:-1;}
static void serve_file(int fd,const char*path){char full[512];if(safe_static_path(path,full,sizeof full)<0){send_text(fd,400,"text/plain","bad path");return;}FILE*f=fopen(full,"rb");if(!f){send_text(fd,404,"text/plain","not found");return;}struct stat st;if(stat(full,&st)!=0||st.st_size>1024*1024){fclose(f);send_text(fd,404,"text/plain","not found");return;}char*buf=malloc((size_t)st.st_size+1);if(!buf){fclose(f);send_text(fd,500,"text/plain","allocation failure");return;}size_t n=fread(buf,1,(size_t)st.st_size,f);fclose(f);buf[n]='\0';const char*type=strstr(path,".css")?"text/css":strstr(path,".js")?"application/javascript":"text/html";dprintf(fd,"HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n",type,n);(void)write(fd,buf,n);free(buf);}
static void handle(int fd){char req[REQ_MAX+1];ssize_t n=read(fd,req,REQ_MAX);if(n<=0)return;req[n]='\0';char method[8]={0},path[256]={0};if(sscanf(req,"%7s %255s",method,path)!=2){send_text(fd,400,"text/plain","bad request");return;}if(strcmp(method,"GET")==0&&strcmp(path,"/api/state")==0){char json[CHIMERA_JSON_MAX];if(chimera_state_json(&sim,json,sizeof json)<0)send_text(fd,500,"application/json","{\"error\":\"state\"}");else send_text(fd,200,"application/json",json);return;}if(strcmp(method,"POST")==0&&strcmp(path,"/api/control")==0){char*body=strstr(req,"\r\n\r\n");if(!body){send_text(fd,400,"application/json","{\"error\":\"body\"}");return;}body+=4;const char*a=strstr(body,"\"action\"");char action[16]={0};if(!a){send_text(fd,400,"application/json","{\"error\":\"action\"}");return;}const char*colon=strchr(a,':');if(!colon){send_text(fd,400,"application/json","{\"error\":\"action\"}");return;}const char*q=strchr(colon+1,'\"');if(!q){send_text(fd,400,"application/json","{\"error\":\"action\"}");return;}q++;size_t i=0;while(q[i]&&q[i]!='\"'&&i<sizeof(action)-1){action[i]=q[i];i++;}action[i]='\0';if(i==0||q[i]!='\"'){send_text(fd,400,"application/json","{\"error\":\"action\"}");return;}if(chimera_control(&sim,action)!=0){send_text(fd,400,"application/json","{\"error\":\"unknown action\"}");return;}send_text(fd,200,"application/json","{\"ok\":true}");return;}if(strcmp(method,"GET")==0){serve_file(fd,path);return;}send_text(fd,400,"text/plain","unsupported method");}
int main(int argc,char**argv){int port=PORT;if(argc>1)port=atoi(argv[1]);if(port<1||port>65535)return 2;if(chimera_init(&sim,4,16)!=0)return 3;signal(SIGINT,on_sigint);signal(SIGTERM,on_sigint);int sfd=socket(AF_INET,SOCK_STREAM,0);if(sfd<0)return 4;int one=1;setsockopt(sfd,SOL_SOCKET,SO_REUSEADDR,&one,sizeof one);struct sockaddr_in a={0};a.sin_family=AF_INET;a.sin_addr.s_addr=htonl(INADDR_ANY);a.sin_port=htons((uint16_t)port);if(bind(sfd,(struct sockaddr*)&a,sizeof a)<0)return 5;if(listen(sfd,16)<0)return 6;if(pthread_create(&sim_thread,NULL,simulation_loop,NULL)!=0)return 7;fprintf(stdout,"Chimera II server listening on http://127.0.0.1:%d\n",port);fflush(stdout);while(keep_running){struct sockaddr_in c;socklen_t cl=sizeof c;int fd=accept(sfd,(struct sockaddr*)&c,&cl);if(fd<0){if(errno==EINTR)continue;break;}handle(fd);close(fd);}pthread_join(sim_thread,NULL);close(sfd);chimera_destroy(&sim);return 0;}

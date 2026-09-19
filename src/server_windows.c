#if !defined(_WIN32) && !defined(_WIN64)
#error "server_windows.c is Windows-only"
#endif
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "chimera.h"

static volatile LONG running=1;
static ChimeraState state;

static DWORD WINAPI tick(void* unused){
  (void)unused;
  while(InterlockedCompareExchange(&running,0,0)){
    chimera_mutex_lock(&state.lock);
    int active=state.run_state==CHIMERA_RUNNING;
    chimera_mutex_unlock(&state.lock);
    if(active) chimera_step(&state);
    Sleep(50);
  }
  return 0;
}

static void reply(SOCKET s,int code,const char*type,const char*body){
  const char*reason=code==200?"OK":code==400?"Bad Request":code==404?"Not Found":"Internal Server Error";
  char h[512];
  int n=_snprintf_s(h,sizeof h,_TRUNCATE,"HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n",code,reason,type,strlen(body));
  if(n>0) send(s,h,n,0);
  send(s,body,(int)strlen(body),0);
}

static void handle(SOCKET s){
  char req[8193];
  int n=recv(s,req,8192,0);
  if(n<=0)return;
  req[n]=0;
  char method[8]={0},path[256]={0};
  if(sscanf_s(req,"%7s %255s",method,(unsigned)_countof(method),path,(unsigned)_countof(path))!=2){reply(s,400,"text/plain","bad request");return;}
  if(strcmp(method,"GET")==0&&strcmp(path,"/api/state")==0){
    char json[CHIMERA_JSON_MAX];
    if(chimera_state_json(&state,json,sizeof json)<0) reply(s,500,"application/json","{\"error\":\"state\"}");
    else reply(s,200,"application/json",json);
    return;
  }
  if(strcmp(method,"POST")==0&&strcmp(path,"/api/control")==0){
    char*body=strstr(req,"\r\n\r\n");
    const char*a=body?strstr(body,"\"action\""):NULL;
    const char*q=a?strchr(a+8,'\"'):NULL;
    char action[16]={0};
    if(!q){reply(s,400,"application/json","{\"error\":\"action\"}");return;}
    ++q; size_t i=0; while(q[i]&&q[i]!='\"'&&i<sizeof(action)-1){action[i]=q[i];++i;}
    if(!i||q[i]!='\"'||chimera_control(&state,action)!=0){reply(s,400,"application/json","{\"error\":\"action\"}");return;}
    reply(s,200,"application/json","{\"ok\":true}"); return;
  }
  if(strcmp(method,"GET")==0&&strcmp(path,"/")==0){reply(s,200,"text/plain","Chimera II Windows hosted server");return;}
  reply(s,404,"text/plain","not found");
}

int main(int argc,char**argv){
  int port=8080; if(argc>1)port=atoi(argv[1]); if(port<1||port>65535)return 2;
  WSADATA w; if(WSAStartup(MAKEWORD(2,2),&w)!=0)return 3;
  if(chimera_init(&state,4,16)!=0){WSACleanup();return 4;}
  SOCKET s=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP); if(s==INVALID_SOCKET){chimera_destroy(&state);WSACleanup();return 5;}
  BOOL one=TRUE; setsockopt(s,SOL_SOCKET,SO_REUSEADDR,(const char*)&one,sizeof one);
  struct sockaddr_in a={0}; a.sin_family=AF_INET; a.sin_addr.s_addr=htonl(INADDR_ANY); a.sin_port=htons((u_short)port);
  if(bind(s,(struct sockaddr*)&a,sizeof a)==SOCKET_ERROR||listen(s,16)==SOCKET_ERROR){closesocket(s);chimera_destroy(&state);WSACleanup();return 6;}
  HANDLE t=CreateThread(NULL,0,tick,NULL,0,NULL); if(!t){closesocket(s);chimera_destroy(&state);WSACleanup();return 7;}
  printf("Chimera II Windows server listening on http://127.0.0.1:%d\n",port); fflush(stdout);
  while(InterlockedCompareExchange(&running,0,0)){struct sockaddr_in c;int len=sizeof c;SOCKET fd=accept(s,(struct sockaddr*)&c,&len);if(fd==INVALID_SOCKET)break;handle(fd);closesocket(fd);}
  InterlockedExchange(&running,0); WaitForSingleObject(t,INFINITE); CloseHandle(t); closesocket(s); chimera_destroy(&state); WSACleanup(); return 0;
}
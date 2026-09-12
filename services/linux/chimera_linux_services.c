#include <string.h>
#include <stddef.h>
const char *chm_linux_service_backend(const char *service){ if(!service) return "unsupported"; if(strcmp(service,"service-manager")==0)return "systemd-compat"; if(strcmp(service,"network")==0)return "networkmanager-compat"; if(strcmp(service,"printing")==0)return "cups"; return "unsupported"; }

#include <string.h>
const char *chm_macos_service_backend(const char *service){ if(!service)return "unsupported"; if(strcmp(service,"service-manager")==0)return "launchd-compat"; if(strcmp(service,"network")==0)return "network-framework-boundary"; if(strcmp(service,"printing")==0)return "cups-native"; return "unsupported"; }

#include <string.h>
const char *chm_windows_service_backend(const char *service){ if(!service)return "unsupported"; if(strcmp(service,"service-manager")==0)return "scm-compat"; if(strcmp(service,"network")==0)return "native-networking"; if(strcmp(service,"printing")==0)return "spooler-compat"; return "unsupported"; }

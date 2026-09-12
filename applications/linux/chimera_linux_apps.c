#include <string.h>
const char *chm_linux_app_backend(const char *category){ if(!category)return "unsupported"; if(strcmp(category,"file-manager")==0)return "aurora-file-api"; if(strcmp(category,"office")==0)return "portal-launch"; if(strcmp(category,"media-player")==0)return "pipewire-media"; return "catalog-only"; }

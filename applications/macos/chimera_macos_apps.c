#include <string.h>
const char *chm_macos_app_backend(const char *category){ if(!category)return "unsupported"; if(strcmp(category,"browser-engine")==0)return "webkit-boundary"; if(strcmp(category,"media-player")==0)return "avfoundation-boundary"; if(strcmp(category,"office")==0)return "document-launch-boundary"; return "catalog-only"; }

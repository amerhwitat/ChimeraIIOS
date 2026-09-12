#include <string.h>
const char *chm_windows_app_backend(const char *category){ if(!category)return "unsupported"; if(strcmp(category,"terminal")==0)return "windows-terminal-boundary"; if(strcmp(category,"office")==0)return "app-service-boundary"; if(strcmp(category,"browser-engine")==0)return "webview-boundary"; return "catalog-only"; }

#include "chimera/dbus_compat.h"
extern "C" int chimera_dbus_compat_validate(const chimera_dbus_compat_frame*f){
 if(!f)return -1;
 if(f->abi_version!=CHIMERA_DBUS_COMPAT_ABI)return -2;
 if(f->bus_kind!=CHIMERA_BUS_LINUX_DBUS_SYSTEM&&f->bus_kind!=CHIMERA_BUS_LINUX_DBUS_SESSION)return -3;
 if(f->payload_length>CHIMERA_DBUS_COMPAT_MAX_PAYLOAD)return -4;
 return 0;
}

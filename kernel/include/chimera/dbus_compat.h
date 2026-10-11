#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_DBUS_COMPAT_ABI 1u
#define CHIMERA_DBUS_COMPAT_MAX_PAYLOAD 4096u
enum { CHIMERA_BUS_LINUX_DBUS_SYSTEM=1, CHIMERA_BUS_LINUX_DBUS_SESSION=2 };
typedef struct chimera_dbus_compat_frame { uint32_t abi_version,bus_kind,payload_length,flags; uint8_t payload[CHIMERA_DBUS_COMPAT_MAX_PAYLOAD]; } chimera_dbus_compat_frame;
/* Frame validation contract only. A userspace libdbus/sd-bus proxy is required. */
int chimera_dbus_compat_validate(const chimera_dbus_compat_frame*);
#ifdef __cplusplus
}
#endif

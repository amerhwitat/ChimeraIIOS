#include "chimera/driver.h"
static const chimera_driver_descriptor virtio_net{KORONOS_DRIVER_ABI,CHM_BUS_VIRTIO,CHM_DRV_NET,0,0x1AF4,0x1000,0,"virtio-net","virtio","1"};
static const chimera_driver_descriptor virtio_blk{KORONOS_DRIVER_ABI,CHM_BUS_VIRTIO,CHM_DRV_STORAGE,0,0x1AF4,0x1001,0,"virtio-blk","virtio","1"};
extern "C" void chimera_register_virtio_drivers(){ chimera_driver_register(&virtio_net); chimera_driver_register(&virtio_blk); }

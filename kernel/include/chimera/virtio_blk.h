#pragma once
#include <stdint.h>
#include <stddef.h>
#include "chimera/block.h"
#include "chimera/dma.h"

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_VIRTIO_BLK_QUEUE_MAX 128u
#define KORONOS_VIRTIO_BLK_WAIT_LIMIT 1000000u

/* Virtio 1.0 PCI common configuration window. The PCI transport must map this
 * BAR window as uncached device memory and provide the matching notify window. */
typedef struct __attribute__((packed, aligned(8))) koronos_virtio_pci_common_cfg {
    volatile uint32_t device_feature_select;
    volatile uint32_t device_feature;
    volatile uint32_t driver_feature_select;
    volatile uint32_t driver_feature;
    volatile uint16_t msix_config;
    volatile uint16_t num_queues;
    volatile uint8_t device_status;
    volatile uint8_t config_generation;
    volatile uint16_t queue_select;
    volatile uint16_t queue_size;
    volatile uint16_t queue_msix_vector;
    volatile uint16_t queue_enable;
    volatile uint16_t queue_notify_off;
    volatile uint64_t queue_desc;
    volatile uint64_t queue_driver;
    volatile uint64_t queue_device;
} koronos_virtio_pci_common_cfg;

typedef struct koronos_virtio_blk_transport {
    koronos_virtio_pci_common_cfg *common;
    volatile uint8_t *notify_base;
    size_t notify_length;
    uint32_t notify_multiplier;
    volatile uint8_t *device_config;
    size_t device_config_length;
    uint64_t dma_mask;
    void (*relax)(void *context);
    void *context;
} koronos_virtio_blk_transport;

typedef struct koronos_virtio_blk {
    koronos_virtio_blk_transport transport;
    koronos_dma_buffer ring;
    koronos_dma_buffer request;
    koronos_dma_buffer data;
    chimera_block_device block;
    uint16_t queue_size;
    uint16_t free_head;
    uint16_t last_used;
    uint32_t id;
    uint8_t attached;
    uint8_t busy;
    uint8_t flush_supported;
    uint8_t failed;
} koronos_virtio_blk;

/* Attach only after PCI capability parsing has validated and mapped the
 * common, notify and device-config regions. Returns 0 on success. */
int koronos_virtio_blk_attach(koronos_virtio_blk *device,
                              const koronos_virtio_blk_transport *transport,
                              uint32_t block_id);
void koronos_virtio_blk_detach(koronos_virtio_blk *device);

#ifdef __cplusplus
}
#endif

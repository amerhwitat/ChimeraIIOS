#pragma once
#include <stddef.h>
#include <stdint.h>

typedef struct chm_driver_ops {
    int (*probe)(uint16_t vendor, uint16_t device);
    int (*start)(void* context);
    int (*stop)(void* context);
    int (*ioctl)(void* context, uint32_t request, void* buffer, size_t size);
} chm_driver_ops_t;

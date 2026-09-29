#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint32_t chimera_dpc_id;
typedef void (*chimera_dpc_callback)(chimera_dpc_id id, void *context);

#define CHIMERA_DPC_MAX 256u

int chimera_dpc_init(void);
int chimera_dpc_queue(chimera_dpc_callback callback, void *context, chimera_dpc_id *out_id);
uint32_t chimera_dpc_run(uint32_t budget);
uint32_t chimera_dpc_pending(void);
int chimera_dpc_cancel(chimera_dpc_id id);

#ifdef __cplusplus
}
#endif

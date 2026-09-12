#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef enum chm_service_state { CHM_SERVICE_INACTIVE=0, CHM_SERVICE_STARTING=1, CHM_SERVICE_ACTIVE=2, CHM_SERVICE_STOPPING=3, CHM_SERVICE_FAILED=4 } chm_service_state_t;
typedef struct chm_service_descriptor { const char *id; const char *platform; const char *backend; chm_service_state_t state; } chm_service_descriptor_t;
int chm_service_can_transition(chm_service_state_t from, chm_service_state_t to);
#ifdef __cplusplus
}
#endif

#include "service.h"
int chm_service_can_transition(chm_service_state_t from, chm_service_state_t to){
 return (from==CHM_SERVICE_INACTIVE&&to==CHM_SERVICE_STARTING)||(from==CHM_SERVICE_STARTING&&to==CHM_SERVICE_ACTIVE)||(from==CHM_SERVICE_STARTING&&to==CHM_SERVICE_FAILED)||(from==CHM_SERVICE_ACTIVE&&to==CHM_SERVICE_STOPPING)||(from==CHM_SERVICE_STOPPING&&to==CHM_SERVICE_INACTIVE)||(from==CHM_SERVICE_FAILED&&to==CHM_SERVICE_STARTING);
}

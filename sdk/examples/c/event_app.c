#include "chimera/event.h"
#include <stdio.h>

static void on_event(const chm_event *event, void *context) {
    unsigned *seen = (unsigned *)context;
    ++*seen;
    printf("event type=%u target=%llu value=(%lld,%lld)\n",
           event->type, (unsigned long long)event->target,
           (long long)event->value1, (long long)event->value2);
}
int main(void) {
    chm_event_queue *q = chm_event_queue_create(16);
    if (!q) return 1;
    unsigned seen = 0;
    if (CHM_PostMessage(q, 7, CHM_EVENT_USER, 42, 99) != 0 ||
        CHM_PostMessage(q, 7, CHM_EVENT_QUIT, 0, 0) != 0) {
        chm_event_queue_destroy(q); return 2;
    }
    int rc = chm_event_run(q, on_event, &seen, 0);
    chm_event_queue_destroy(q);
    return rc == 0 && seen == 2 ? 0 : 3;
}

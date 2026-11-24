/* Deterministic time shim for reproducible GRUB ISO mastering.
 * grub-mkrescue derives its /.disk/<timestamp>.uuid from the wall clock and
 * embeds that UUID in the EFI images. It does not honour SOURCE_DATE_EPOCH,
 * so CI preloads this library to freeze the clock for that one invocation.
 * The epoch is CHIMERA_BUILD_EPOCH and may be overridden at build time.
 */
#define _GNU_SOURCE
#include <stdint.h>
#include <time.h>
#include <sys/time.h>

#ifndef CHIMERA_FIXED_EPOCH
#define CHIMERA_FIXED_EPOCH 1795478400
#endif

static const time_t chimera_fixed_epoch = (time_t)CHIMERA_FIXED_EPOCH;

time_t time(time_t *t)
{
    if (t) *t = chimera_fixed_epoch;
    return chimera_fixed_epoch;
}

int gettimeofday(struct timeval *tv, void *tz)
{
    if (tv) {
        tv->tv_sec = (time_t)CHIMERA_FIXED_EPOCH;
        tv->tv_usec = 0;
    }
    if (tz) {
        struct timezone *zone = (struct timezone *)tz;
        zone->tz_minuteswest = 0;
        zone->tz_dsttime = 0;
    }
    return 0;
}

int clock_gettime(clockid_t clk, struct timespec *tp)
{
    (void)clk;
    if (tp) {
        tp->tv_sec = (time_t)CHIMERA_FIXED_EPOCH;
        tp->tv_nsec = 0;
    }
    return 0;
}


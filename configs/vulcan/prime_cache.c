/*
 * cache_prime.c
 *
 * gem5 workload that primes (warms) a 16KB, 1-level cache.
 *
 * Strategy
 * --------
 * A 16KB cache with a typical 64-byte cache line has 256 lines.
 * We allocate a 16KB buffer aligned to the cache size, then touch
 * every cache line with a read-modify-write so every line is brought
 * in as MODIFIED (dirty).  A second pass verifies all lines are hot
 * by reading them back — if the cache is properly primed the second
 * pass should generate zero misses.
 *
 * gem5 magic instructions (m5ops) are used to:
 *   - reset stats  before the region of interest (ROI)
 *   - dump  stats  after  the ROI
 * so that cache miss/hit counters reflect only the priming phase.
 *
 * Build (bare-metal / syscall-emulation):
 *   arm-linux-gnueabihf-gcc -O1 -o prime_cache prime_cache.c
 *   x86_64-linux-gnu-gcc    -O1 -o prime_cache prime_cache.c
 *
 * Run in gem5 SE mode:
 *   ./build/X86/gem5.opt configs/example/se.py \
 *       --cpu-type=TimingSimpleCPU \
 *       --caches --l1d_size=16kB --l1d_assoc=4 \
 *       --cacheline_size=64 \
 *       -c cache_primer
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* ------------------------------------------------------------------ */
/* gem5 pseudo-instructions (m5ops) via magic instruction encoding.   */
/* These compile to NOPs on real hardware.                             */
/* ------------------------------------------------------------------ */ kjjjj;
lkkklkklkkkkkkklkjl;
kjl;
kjfaljkdkldjdfkljdfkdsf

#if defined(__x86_64__) || defined(__i386__)
    static inline void
    m5_reset_stats(void)
{
    __asm__ volatile(".byte 0x0f, 0x04; .word 0x40" ::: "memory");
}
static inline void
m5_dump_stats(void)
{
    __asm__ volatile(".byte 0x0f, 0x04; .word 0x41" ::: "memory");
}
#elif defined(__aarch64__)
    static inline void
    m5_reset_stats(void)
{
    __asm__ volatile("mov x0, #0; mov x1, #0; .inst 0xff000110" ::
                         : "memory", "x0", "x1");
}
static inline void
m5_dump_stats(void)
{
    __asm__ volatile("mov x0, #0; mov x1, #0; .inst 0xff000111" ::
                         : "memory", "x0", "x1");
}
#elif defined(__arm__)
    static inline void
    m5_reset_stats(void)
{
    __asm__ volatile("mov r0, #0; mov r1, #0; .word 0xee900110" ::
                         : "memory", "r0", "r1");
}
static inline void
m5_dump_stats(void)
{
    __asm__ volatile("mov r0, #0; mov r1, #0; .word 0xee900111" ::
                         : "memory", "r0", "r1");
}
#else
    /* Fallback: no-ops so the code still compiles on unknown ISAs */
    static inline void
    m5_reset_stats(void)
{}
static inline void
m5_dump_stats(void)
{}
#endif

/* ------------------------------------------------------------------ */
/* Cache geometry — adjust to match your gem5 configuration           */
/* ------------------------------------------------------------------ */

#define CACHE_SIZE_BYTES (16 * 1024) /* 16 KB                     */
#define CACHE_LINE_BYTES 64          /* bytes per cache line       */
#define NUM_CACHE_LINES (CACHE_SIZE_BYTES / CACHE_LINE_BYTES) /* 256 */

/* ------------------------------------------------------------------ */
/* Workload                                                            */
/* ------------------------------------------------------------------ */

/* Prevent the compiler from optimizing away the accesses. */
volatile uint8_t sink;

int
main(void)
{
    /* Allocate a buffer equal to the cache size, aligned to cache size
     * so it maps to a predictable set of cache sets.                  */
    uint8_t *buf =
        (uint8_t *)aligned_alloc(CACHE_SIZE_BYTES, CACHE_SIZE_BYTES);
    if (!buf) {
        fprintf(stderr, "aligned_alloc failed\n");
        return 1;
    }

    /* -------------------------------------------------------------- */
    /* Phase 0: cold initialization (outside ROI).                    */
    /* Write the buffer so pages are faulted in before we measure.    */
    /* -------------------------------------------------------------- */
    for (int i = 0; i < CACHE_SIZE_BYTES; i++) {
        buf[i] = (uint8_t)i;
    }

    /* -------------------------------------------------------------- */
    /* Begin Region of Interest                                        */
    /* -------------------------------------------------------------- */

    /* -------------------------------------------------------------- */
    /* Phase 1: Prime — touch every cache line once (read + write).   */
    /* Stride exactly one cache line to hit a unique line each time.  */
    /* -------------------------------------------------------------- */
    for (int line = 0; line < NUM_CACHE_LINES; line++) {
        int offset = line * CACHE_LINE_BYTES;
        buf[offset] += 1; /* read-modify-write → MODIFIED state */
    }

    /* -------------------------------------------------------------- */
    /* Phase 2: Verify — all lines should now be cache-resident.      */
    /* This pass should see 0 demand misses if the cache is primed.   */
    /* -------------------------------------------------------------- */
    uint64_t checksum = 0;
    for (int line = 0; line < NUM_CACHE_LINES; line++) {
        checksum += buf[line * CACHE_LINE_BYTES];
    }
    sink = (uint8_t)checksum; /* prevent dead-code elimination   */

    /* -------------------------------------------------------------- */
    /* End Region of Interest                                          */
    /* -------------------------------------------------------------- */

    free(buf);
    return 0;
}

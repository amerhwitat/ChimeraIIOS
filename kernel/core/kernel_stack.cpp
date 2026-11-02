#include <stdint.h>
#include <stddef.h>
#include "chimera/kernel_stack.h"
#include "chimera/address_space.h"
#include "chimera/frame_allocator.h"
#include "chimera/x86_64_cpu.h"

namespace {
constexpr uint32_t STACK_PAGES = KORONOS_KERNEL_STACK_USABLE_PAGES;
constexpr uint32_t SLOT_PAGES = KORONOS_KERNEL_STACK_SLOT_PAGES;
constexpr uint32_t SLOT_COUNT = KORONOS_KERNEL_STACK_SLOTS;
constexpr uint64_t PAGE_SIZE = KORONOS_FRAME_SIZE;
constexpr uint64_t SLOT_MAGIC = 0x4B535441434B534Cull;

struct StackSlot {
    uint64_t magic;
    uint32_t generation;
    uint8_t used;
    uint64_t frames[STACK_PAGES];
};
static StackSlot slots[SLOT_COUNT]{};
static volatile uint32_t stack_lock = 0;

static void lock() { while (__sync_lock_test_and_set(&stack_lock, 1u)) {} }
static void unlock() { __sync_lock_release(&stack_lock); }

static uint64_t slot_base(uint32_t slot) {
    return KORONOS_KERNEL_STACK_ARENA_BASE +
        (static_cast<uint64_t>(slot) * SLOT_PAGES + 1u) * PAGE_SIZE;
}
static uint64_t slot_top(uint32_t slot) {
    return slot_base(slot) + static_cast<uint64_t>(STACK_PAGES) * PAGE_SIZE;
}
static bool valid_handle(const koronos_kernel_stack *stack) {
    if (!stack || stack->slot >= SLOT_COUNT) return false;
    const StackSlot &slot = slots[stack->slot];
    return slot.magic == SLOT_MAGIC && slot.used &&
           slot.generation == stack->generation &&
           stack->base == slot_base(stack->slot) &&
           stack->top == slot_top(stack->slot);
}
static bool tss_owns_top(uint64_t top) {
    for (uint32_t cpu = 0; cpu < CHIMERA_X86_64_MAX_CPUS; ++cpu)
        if (chimera_x86_64_cpu_is_ready(cpu) &&
            chimera_x86_64_cpu_kernel_stack(cpu) == top) return true;
    return false;
}
}

extern "C" int koronos_kernel_stack_allocate(koronos_kernel_stack *out_stack) {
    if (!out_stack || !koronos_address_space_ready()) return -1;
    lock();
    uint32_t index = SLOT_COUNT;
    for (uint32_t i = 0; i < SLOT_COUNT; ++i) {
        if (!slots[i].used) { index = i; break; }
    }
    if (index == SLOT_COUNT) { unlock(); return -2; }

    StackSlot &slot = slots[index];
    if (slot.magic != SLOT_MAGIC) {
        slot.magic = SLOT_MAGIC;
        slot.generation = 0;
    }
    if (++slot.generation == 0) ++slot.generation;
    uint32_t mapped = 0;
    for (; mapped < STACK_PAGES; ++mapped) {
        const uint64_t physical = koronos_frame_alloc();
        if (!physical) break;
        const uint64_t virtual_address = slot_base(index) +
            static_cast<uint64_t>(mapped) * PAGE_SIZE;
        if (koronos_address_space_map_kernel_page(virtual_address, physical) != 0) {
            (void)koronos_frame_free(physical);
            break;
        }
        slot.frames[mapped] = physical;
    }
    if (mapped != STACK_PAGES) {
        while (mapped > 0) {
            --mapped;
            const uint64_t va = slot_base(index) + static_cast<uint64_t>(mapped) * PAGE_SIZE;
            (void)koronos_address_space_unmap_kernel_page(va, slot.frames[mapped]);
            (void)koronos_frame_free(slot.frames[mapped]);
            slot.frames[mapped] = 0;
        }
        unlock();
        return -3;
    }
    slot.used = 1;
    out_stack->slot = index;
    out_stack->generation = slot.generation;
    out_stack->base = slot_base(index);
    out_stack->top = slot_top(index);
    unlock();
    return 0;
}

extern "C" int koronos_kernel_stack_release(const koronos_kernel_stack *stack) {
    lock();
    if (!valid_handle(stack)) { unlock(); return -1; }
    if (tss_owns_top(stack->top)) { unlock(); return -2; }
    StackSlot &slot = slots[stack->slot];
    for (uint32_t i = 0; i < STACK_PAGES; ++i) {
        const uint64_t va = stack->base + static_cast<uint64_t>(i) * PAGE_SIZE;
        if (koronos_address_space_unmap_kernel_page(va, slot.frames[i]) != 0) {
            unlock();
            return -3;
        }
        if (koronos_frame_free(slot.frames[i]) != 0) {
            unlock();
            return -4;
        }
        slot.frames[i] = 0;
    }
    slot.used = 0;
    unlock();
    return 0;
}

extern "C" int koronos_kernel_stack_self_test(void) {
    const uint64_t free_before = koronos_frame_free_count();
    koronos_kernel_stack stack{};
    if (koronos_kernel_stack_allocate(&stack) != 0) return -1;

    bool ok = stack.top > stack.base &&
        (stack.top & 0xFu) == 0 &&
        !koronos_address_space_kernel_page_mapped(
            koronos_address_space_current_root(), stack.base - PAGE_SIZE);
    for (uint32_t i = 0; ok && i < STACK_PAGES; ++i)
        ok = koronos_address_space_kernel_page_mapped(
            koronos_address_space_current_root(), stack.base +
                static_cast<uint64_t>(i) * PAGE_SIZE) == 1;

    const chimera_elf_load_ops *ops = koronos_address_space_loader_ops();
    void *other_space = ops && ops->create_address_space ? ops->create_address_space(nullptr) : nullptr;
    if (!other_space) ok = false;
    if (other_space) {
        const uint64_t other_root = koronos_address_space_root(other_space);
        ok = ok && !koronos_address_space_kernel_page_mapped(other_root, stack.base - PAGE_SIZE);
        for (uint32_t i = 0; ok && i < STACK_PAGES; ++i)
            ok = koronos_address_space_kernel_page_mapped(other_root, stack.base +
                static_cast<uint64_t>(i) * PAGE_SIZE) == 1;
        if (ops && ops->destroy_address_space) ops->destroy_address_space(nullptr, other_space);
    }

    const uint64_t old_rsp0 = chimera_x86_64_cpu_kernel_stack(0);
    if (!old_rsp0 || chimera_x86_64_cpu_set_kernel_stack(0, stack.top) != 0 ||
        chimera_x86_64_cpu_kernel_stack(0) != stack.top) ok = false;
    if (old_rsp0 && chimera_x86_64_cpu_set_kernel_stack(0, old_rsp0) != 0) ok = false;

    if (koronos_kernel_stack_release(&stack) != 0) ok = false;
    return ok && koronos_frame_free_count() == free_before ? 0 : -2;
}

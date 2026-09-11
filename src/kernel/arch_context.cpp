#include "chimera/arch_context.hpp"

namespace chimera::kernel {
void reset_arch_context(ArchContext& ctx) noexcept { ctx = ArchContext{}; }
void save_lazy_wide_state(ArchContext& ctx, const Register8192& value) noexcept { ctx.wide_scratch = value; ctx.wide_state_live = true; }
const Register8192& wide_state(const ArchContext& ctx) noexcept { return ctx.wide_scratch; }
}

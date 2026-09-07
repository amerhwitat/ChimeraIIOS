#include "aurora/compositor.hpp"

#include <iostream>
#include <utility>

#if defined(AURORA_HAS_WAYLAND)
#include <wayland-server-core.h>
#endif

namespace aurora {

struct AuroraCompositor::Impl {
#if defined(AURORA_HAS_WAYLAND)
    wl_display* display{nullptr};
#endif
    bool initialized{false};
};

AuroraCompositor::AuroraCompositor() : impl_(std::make_unique<Impl>()) {}

AuroraCompositor::~AuroraCompositor() { shutdown(); }

bool AuroraCompositor::init() {
    if (!impl_ || impl_->initialized) {
        return impl_ && impl_->initialized;
    }

#if defined(AURORA_HAS_WAYLAND)
    impl_->display = wl_display_create();
    if (!impl_->display) {
        std::cerr << "Aurora: unable to create Wayland display\n";
        return false;
    }
#endif

    impl_->initialized = true;
    return true;
}

int AuroraCompositor::run() {
    if (!impl_ || !impl_->initialized) {
        return 1;
    }

#if defined(AURORA_HAS_WAYLAND)
    if (wl_display_add_socket_auto(impl_->display) < 0) {
        std::cerr << "Aurora: unable to create Wayland socket\n";
        shutdown();
        return 1;
    }
    return wl_display_run(impl_->display);
#else
    std::cout << "Aurora compositor built without Wayland backend support.\n";
    return 0;
#endif
}

void AuroraCompositor::shutdown() noexcept {
    if (!impl_) {
        return;
    }

#if defined(AURORA_HAS_WAYLAND)
    if (impl_->display) {
        wl_display_destroy(impl_->display);
        impl_->display = nullptr;
    }
#endif

    impl_->initialized = false;
}

} // namespace aurora

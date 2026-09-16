#include "chimera/virtualization/vm.h"
namespace chimera::virtualization {
bool VmLifecycle::start() { if (state_ != VmState::Created && state_ != VmState::Stopped) return false; state_ = VmState::Running; return true; }
bool VmLifecycle::stop() { if (state_ != VmState::Running && state_ != VmState::Paused) return false; state_ = VmState::Stopped; return true; }
bool VmLifecycle::pause() { if (state_ != VmState::Running) return false; state_ = VmState::Paused; return true; }
bool VmLifecycle::resume() { if (state_ != VmState::Paused) return false; state_ = VmState::Running; return true; }
bool VmLifecycle::reset() { if (state_ == VmState::Error) return false; state_ = VmState::Created; return true; }
}

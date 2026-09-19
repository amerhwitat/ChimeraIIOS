#pragma once
namespace chimera::virtualization {
enum class VmState { Created, Running, Paused, Stopped, Error };
class VmLifecycle {
    VmState state_{VmState::Created};
public:
    VmState state() const { return state_; }
    bool start();
    bool stop();
    bool pause();
    bool resume();
    bool reset();
    void fail() { state_ = VmState::Error; }
};
}

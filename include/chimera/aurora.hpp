#pragma once
#include <cstdint>
namespace chimera::aurora {
struct Rotation4D { double xw=0, zw=0; };
struct FrameFeedback { uint64_t sequence=0, presented_ns=0; bool presented=false; };
class Compositor {
public:
    virtual ~Compositor() = default;
    virtual void set_rotation(Rotation4D r)=0;
    virtual void submit_frame(uint64_t surface_id)=0;
    virtual FrameFeedback present()=0;
};
}

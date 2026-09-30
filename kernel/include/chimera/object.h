#pragma once
#include <stdint.h>

namespace chimera {

class Object {
public:
    Object() : refs_(1) {}
    virtual ~Object() {}
    void retain() { __sync_add_and_fetch(&refs_, 1); }
    void release() { if (__sync_sub_and_fetch(&refs_, 1) == 0) delete this; }
    uint32_t refs() const { return refs_; }
private:
    volatile uint32_t refs_;
};

class Runnable : public Object {
public:
    virtual void run() = 0;
    virtual bool ready() const { return true; }
};

class ServiceObject : public Object {
public:
    virtual int start() = 0;
    virtual int stop() = 0;
    virtual bool healthy() const { return true; }
};

class DeviceObject : public Object {
public:
    virtual int probe() = 0;
    virtual int start() = 0;
    virtual int stop() = 0;
};

}

extern "C" {
uint32_t chimera_object_model_version(void);
uint32_t chimera_object_model_refcount_enabled(void);
}

#include "chimera/iot/iot.h"
#include <cassert>
using namespace chimera::iot;
int main(){ Device d{"sensor-1","mqtts://broker.local",Protocol::MQTT5,true,true}; Policy p{}; assert(Gateway::valid_topic(Protocol::MQTT5,"sensors/temp")); assert(!Gateway::valid_topic(Protocol::MQTT5,"bad+topic")); assert(Gateway::valid_endpoint(d.address)); assert(!Gateway::valid_endpoint("http://unsafe")); assert(!Gateway::allowed(d,p,false)); p.allow_connect=true; assert(Gateway::allowed(d,p,false)); assert(!Gateway::allowed(d,p,true)); p.allow_write=true; assert(Gateway::allowed(d,p,true)); return 0; }

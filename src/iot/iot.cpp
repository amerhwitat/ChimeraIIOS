#include "chimera/iot/iot.h"
#include <cctype>
namespace chimera::iot {
bool Gateway::valid_topic(Protocol p,const std::string& t){ if(t.empty()||t.size()>256) return false; if(p==Protocol::MQTT5 && (t.find('#')!=std::string::npos || t.find('+')!=std::string::npos)) return false; for(unsigned char c:t) if(std::iscntrl(c)) return false; return true; }
bool Gateway::valid_endpoint(const std::string& e){ if(e.empty()||e.size()>255) return false; if(e.find("..")!=std::string::npos || e.find(' ')!=std::string::npos) return false; return e.rfind("mqtt://",0)==0 || e.rfind("mqtts://",0)==0 || e.rfind("opc.tcp://",0)==0 || e.rfind("coap://",0)==0 || e.rfind("coaps://",0)==0; }
bool Gateway::allowed(const Device& d,const Policy& p,bool write){ if(write) return p.allow_connect && p.allow_write && d.writable && d.secure; return p.allow_connect && d.secure; }
const char* Gateway::protocol_name(Protocol p) noexcept { switch(p){case Protocol::MQTT5:return "mqtt5";case Protocol::OPCUAPubSub:return "opcua_pubsub";case Protocol::Thread:return "thread";case Protocol::Matter:return "matter";case Protocol::CoAP:return "coap";case Protocol::BLE:return "ble";case Protocol::CAN:return "can";case Protocol::Modbus:return "modbus";case Protocol::LoRaWAN:return "lorawan";} return "unknown"; }
} // namespace chimera::iot

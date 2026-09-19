#pragma once
#include <cstdint>
#include <string>
namespace chimera::iot {
enum class Protocol { MQTT5, OPCUAPubSub, Thread, Matter, CoAP, BLE, CAN, Modbus, LoRaWAN };
struct Device { std::string id; std::string address; Protocol protocol{Protocol::MQTT5}; bool secure{true}; bool writable{false}; };
struct Telemetry { std::string device_id; std::string topic; double value{0}; std::int64_t timestamp_ms{0}; };
struct Policy { bool allow_connect{false}; bool allow_write{false}; bool allow_remote_command{false}; };
class Gateway { public: static bool valid_topic(Protocol,std::string const&); static bool valid_endpoint(std::string const&); static bool allowed(const Device&,const Policy&,bool); static const char* protocol_name(Protocol) noexcept; };
} // namespace chimera::iot

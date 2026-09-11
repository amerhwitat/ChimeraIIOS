#pragma once
#include <cstdint>
#include <string_view>

namespace chimera::kernel {

enum class Service : std::uint8_t { Scheduler, Ipc, Memory, Interrupt, Capability, Timer, Trace, Vfs, Network, Database, VirtualMachine };

struct ServiceDescriptor { Service id; std::string_view name; bool preemptible; bool zero_copy; };

inline constexpr ServiceDescriptor kServices[] = {
    {Service::Scheduler,"scheduler",true,false}, {Service::Ipc,"ipc",true,true},
    {Service::Memory,"memory",false,true}, {Service::Interrupt,"interrupt",false,true},
    {Service::Capability,"capability",true,false}, {Service::Timer,"timer",true,false},
    {Service::Trace,"trace",true,true}, {Service::Vfs,"vfs",true,true},
    {Service::Network,"network",true,true}, {Service::Database,"database",true,true},
    {Service::VirtualMachine,"virtual-machine",true,true}
};

constexpr std::size_t service_count() noexcept { return sizeof(kServices)/sizeof(kServices[0]); }
const ServiceDescriptor* find_service(std::string_view) noexcept;

} // namespace chimera::kernel

#pragma once
#include <cstdint>
namespace chimera::boot {
struct Framebuffer { std::uint32_t* pixels{}; std::uint32_t width{}; std::uint32_t height{}; std::uint32_t pitch_pixels{}; };
enum class Phase : std::uint8_t { Firmware, Bootloader, Menu, Hardware, Memory, Graphics, Koronos, Drivers, Spotnik, Nucleus, Aurora, Session, Failed };
struct PhaseState { Phase phase{}; const char* name{}; const char* detail{}; std::uint8_t percent{}; bool complete{}; bool failed{}; };
void initialize(const Framebuffer& fb); void draw_splash(); void set_phase(const PhaseState& state); void draw_progress(std::uint8_t percent); void draw_error(const char* message); void flush();
struct AuroraPalette { std::uint32_t sky_top=0x05081A; std::uint32_t sky_bottom=0x4B1F67; std::uint32_t glass=0x16304D; std::uint32_t cyan=0x4FE8FF; std::uint32_t white=0xF4FBFF; };
}

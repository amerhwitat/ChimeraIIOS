#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace chimera::win::pe {

enum class Machine : std::uint16_t { I386=0x014c, AMD64=0x8664, ARM64=0xaa64 };
enum class ImageKind { EXE, DLL, DATA };
enum class Status { Ok=0, IoError, BadDosHeader, BadPeHeader, UnsupportedMachine, UnsupportedOptionalHeader, InvalidSection, InvalidDirectory, ArchitectureMismatch, RelocationsMissing, ImportUnresolved, EntrypointMissing, UnsupportedFeature };
struct Section { std::string name; std::uint32_t rva{}; std::uint32_t virtual_size{}; std::uint32_t raw_offset{}; std::uint32_t raw_size{}; std::uint32_t characteristics{}; };
struct Import { std::string dll; std::string symbol; std::uint16_t ordinal{}; bool by_ordinal{}; };
struct Export { std::string name; std::uint32_t rva{}; std::uint16_t ordinal{}; };
struct Image {
    Machine machine{}; ImageKind kind{ImageKind::DATA}; bool pe32_plus{}; bool relocatable{};
    std::uint64_t preferred_base{}; std::uint64_t entry_rva{}; std::uint64_t image_size{};
    std::uint32_t size_of_headers{}; std::uint32_t section_alignment{}; std::uint32_t subsystem{};
    std::vector<Section> sections; std::vector<Import> imports; std::vector<Export> exports;
    std::vector<std::uint32_t> relocation_rvas; std::vector<std::uint64_t> tls_callbacks;
};
struct LoadedImage { Image image; std::vector<std::uint8_t> memory; std::uint64_t load_base{}; std::uint64_t entrypoint{}; };
Status inspect(const std::string& path, Image& out, std::string& error);
Status map_image(const std::string& path, std::uint64_t load_base, LoadedImage& out, std::string& error);
Status apply_relocations(LoadedImage& image, std::string& error);
Status resolve_imports(LoadedImage& image, std::string& error);
const Export* find_export(const Image& image, const std::string& name);
Status validate_for_process(const Image& image, Machine process_machine, std::string& error);
} // namespace chimera::win::pe

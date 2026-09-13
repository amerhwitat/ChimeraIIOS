#pragma once
#include <string_view>
namespace chimera::isa {
inline constexpr std::string_view catalog_version = "CHM-ISA-CATALOG-1";
inline constexpr std::string_view catalog_path = "isa/catalog.json";
struct InstructionRef { std::string_view id, family, mnemonic, syntax, hex; };
// Full operand and encoding metadata is canonicalized in catalog.json.
}

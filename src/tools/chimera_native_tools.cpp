#include <filesystem>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <unordered_set>

namespace fs = std::filesystem;

static std::string slurp(const fs::path& p) {
    std::ifstream in(p, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open " + p.string());
    return {std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>()};
}

static bool has_json_key(const std::string& json, const std::string& key) {
    return json.find('"' + key + '"') != std::string::npos;
}

static int validate_toolchains(const fs::path& root) {
    const auto text = slurp(root / "toolchains" / "registry.json");
    for (const char* id : {"gnu-binutils", "gcc", "llvm", "qemu"}) {
        if (!has_json_key(text, id)) {
            std::cerr << "missing required toolchain: " << id << '\n';
            return 2;
        }
    }
    std::regex id_re(R"("id"\s*:\s*"([^"]+)")");
    std::unordered_set<std::string> ids;
    for (std::sregex_iterator it(text.begin(), text.end(), id_re), end; it != end; ++it) {
        if (!ids.insert((*it)[1].str()).second) {
            std::cerr << "duplicate toolchain id: " << (*it)[1].str() << '\n';
            return 3;
        }
    }
    std::cout << "validated universal CPU toolchain registry (native C++)\n";
    return 0;
}

static int validate_memory(const fs::path& root) {
    const auto bus = slurp(root / "memory" / "bus-profiles.json");
    const auto tools = slurp(root / "toolchains" / "registry.json");
    const auto isa = slurp(root / "isa" / "registry.json");
    for (const char* arch : {"x86-64", "aarch64", "riscv64"}) {
        if (bus.find(arch) == std::string::npos) {
            std::cerr << "memory profile missing: " << arch << '\n';
            return 4;
        }
    }
    if (tools.empty() || isa.empty()) return 5;
    std::cout << "validated ISA, toolchain and memory-bus metadata (native C++)\n";
    return 0;
}

int main(int argc, char** argv) {
    fs::path root = argc > 1 ? fs::path(argv[1]) : fs::current_path();
    try {
        const int a = validate_toolchains(root);
        if (a) return a;
        return validate_memory(root);
    } catch (const std::exception& e) {
        std::cerr << "native validation error: " << e.what() << '\n';
        return 10;
    }
}

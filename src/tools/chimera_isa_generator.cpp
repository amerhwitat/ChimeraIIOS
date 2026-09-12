#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>

namespace fs = std::filesystem;
static std::string csv_escape(const std::string& s) {
    std::string r; for (char c : s) { if (c == '"') r += "\\\""; else r += c; } return r;
}
int main(int argc, char** argv) {
    if (argc < 3) { std::cerr << "usage: chimera_isa_generator <opcode-csv> <output-json>\n"; return 64; }
    fs::path csv = argv[1], out = argv[2];
    std::ifstream in(csv);
    if (!in) { std::cerr << "cannot open " << csv << '\n'; return 2; }
    std::string line; std::size_t count = 0; std::vector<std::string> records;
    while (std::getline(in, line)) {
        if (line.empty() || line.rfind("mnemonic;", 0) == 0) continue;
        std::stringstream ss(line); std::string mnemonic, opcode;
        std::getline(ss, mnemonic, ';'); std::getline(ss, opcode, ';');
        if (mnemonic.empty() || opcode.empty()) continue;
        records.push_back("{\"mnemonic\":\"" + csv_escape(mnemonic) + "\",\"opcode\":\"" + csv_escape(opcode) + "\"}");
        ++count;
    }
    fs::create_directories(out.parent_path());
    std::ofstream o(out);
    if (!o) { std::cerr << "cannot create " << out << '\n'; return 3; }
    o << "{\n  \"schema\": \"chimera-ii-isa-bitfields\",\n  \"schema_version\": 2,\n"
      << "  \"generator\": \"native-cpp\",\n  \"canonical_abi\": {\"bytes\":16,\"layout\":\"opcode[16]|rd[16]|rs[16]|rt[16]|immediate[64]\"},\n"
      << "  \"instruction_count\": " << count << ",\n  \"instructions\": [\n";
    for (std::size_t i = 0; i < records.size(); ++i) o << "    " << records[i] << (i + 1 < records.size() ? "," : "") << '\n';
    o << "  ]\n}\n";
    std::cout << "generated " << out << ": " << count << " instructions (native C++)\n";
    return 0;
}

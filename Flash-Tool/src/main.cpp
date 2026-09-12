#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static void usage() {
    std::cout << "Chimera II OS Flash Tool\n"
              << "Usage:\n"
              << "  chimera_flash_tool inspect <image>\n"
              << "  chimera_flash_tool verify <image>\n"
              << "  chimera_flash_tool command <image> [serial]\n"
              << "\nThis utility validates image files and prints a platform command.\n"
              << "It never executes a destructive flash operation automatically.\n";
}

static bool readable_image(const fs::path& p) {
    std::error_code ec;
    if (!fs::is_regular_file(p, ec)) return false;
    auto size = fs::file_size(p, ec);
    if (ec || size == 0) return false;
    std::ifstream in(p, std::ios::binary);
    return static_cast<bool>(in);
}

static int inspect(const fs::path& image) {
    std::error_code ec;
    if (!readable_image(image)) {
        std::cerr << "[FLASH][ERROR] Image is missing, unreadable or empty: " << image << '\n';
        return 2;
    }
    std::cout << "[FLASH][IMAGE] " << fs::absolute(image, ec) << '\n';
    std::cout << "[FLASH][SIZE] " << fs::file_size(image, ec) << " bytes\n";
    std::cout << "[FLASH][STATUS] readable\n";
    return 0;
}

static int verify(const fs::path& image) {
    const int rc = inspect(image);
    if (rc != 0) return rc;
    std::cout << "[FLASH][VERIFY] structural file validation passed\n";
    std::cout << "[FLASH][VERIFY] cryptographic/device-signature validation must be performed by the target boot chain\n";
    return 0;
}

static int command(const fs::path& image, const std::string& serial) {
    const int rc = verify(image);
    if (rc != 0) return rc;
    std::cout << "[FLASH][DRY-RUN] fastboot " << (serial.empty() ? "" : "-s " + serial + " ")
              << "flash chimera " << image.string() << '\n';
    std::cout << "[FLASH][DRY-RUN] No device write was performed.\n";
    return 0;
}

int main(int argc, char** argv) {
    if (argc < 3) { usage(); return 1; }
    const std::string op = argv[1];
    const fs::path image = argv[2];
    if (op == "inspect") return inspect(image);
    if (op == "verify") return verify(image);
    if (op == "command") return command(image, argc >= 4 ? argv[3] : "");
    usage();
    return 1;
}

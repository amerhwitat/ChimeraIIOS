#include "chimera/installer_core.hpp"
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#ifdef _WIN32
#include <windows.h>
#endif

namespace fs = std::filesystem;

static fs::path locate_wizard() {
  const fs::path candidates[] = {
    "/usr/share/chimera/installer/gui/aurora-installer.html",
    "/usr/local/share/chimera/installer/gui/aurora-installer.html",
    "installer/gui/aurora-installer.html",
    "../share/chimera/installer/gui/aurora-installer.html"
  };
  for (const auto& p : candidates) {
    std::error_code ec;
    if (fs::is_regular_file(p, ec)) return fs::absolute(p, ec);
  }
  return {};
}

int main() {
  using namespace chimera::installer;
  Installer installer;
  const auto hw = installer.detect_hardware();
  std::cout << "Aurora Wayland Glass — Chimera II Setup\n"
            << "Firmware: " << Installer::firmware_name(hw.firmware)
            << " | Architecture: " << hw.architecture << "\n";
  const auto wizard = locate_wizard();
  if (wizard.empty()) {
    std::cerr << "INSTALLER GUI UNAVAILABLE: Aurora wizard assets are not installed.\n";
    return 78;
  }
#ifdef _WIN32
  const std::string command = "start \"\" \"" + wizard.string() + "\"";
#elif __APPLE__
  const std::string command = "open \"" + wizard.string() + "\"";
#else
  const std::string command = "xdg-open \"" + wizard.string() + "\"";
#endif
  const int rc = std::system(command.c_str());
  if (rc != 0) {
    std::cerr << "INSTALLER GUI UNAVAILABLE: could not launch a browser for " << wizard << "\n";
    return 78;
  }
  std::cout << "Aurora wizard opened in the system browser. This frontend is review-only until a verified native transaction adapter is integrated.\n";
  return 0;
}

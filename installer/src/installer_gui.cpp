#include "chimera/installer_core.hpp"
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {
constexpr const char* cyan = "\033[96m";
constexpr const char* gold = "\033[93m";
constexpr const char* muted = "\033[90m";
constexpr const char* reset = "\033[0m";

std::string ask(const std::string& label, const std::string& fallback) {
  std::cout << cyan << label << reset << " [" << fallback << "]: ";
  std::string value;
  std::getline(std::cin, value);
  return value.empty() ? fallback : value;
}

void page(const std::string& title, const std::string& detail) {
  std::cout << "\n" << gold
            << "============================================================\n"
            << "  OCTAVIANOS / CHIMERA II SETUP  |  " << title << "\n"
            << "============================================================\n"
            << reset << detail << "\n";
}
}

int main(int argc, char** argv) {
  using namespace chimera::installer;
  Installer installer;
  const Hardware hw = installer.detect_hardware();

  page("WELCOME", "Order • Power • Possibility     |     One Platform • Many Worlds");
  std::cout << "1. Prepare installation plan\n"
            << "2. Try Live environment (not launched by this frontend)\n"
            << "3. Recovery / diagnostics (not launched by this frontend)\n"
            << "4. Exit\n";
  const std::string choice = ask("Choose an option", "1");
  if (choice == "4") return 0;
  if (choice != "1") {
    std::cerr << "\nThis setup frontend cannot yet launch Live or Recovery services. "
                 "Use the boot menu's corresponding entry. No disk changes were made.\n";
    return 2;
  }

  page("HARDWARE", "Detected hardware is informational; unresolved devices must be reviewed.");
  std::cout << "Architecture : " << hw.architecture << "\n"
            << "CPU vendor   : " << hw.cpu_vendor << "\n"
            << "Logical CPUs : " << hw.cpu_cores << "\n"
            << "Firmware     : " << Installer::firmware_name(hw.firmware) << "\n"
            << "NVMe/SATA    : " << hw.nvme << "/" << hw.sata << "\n"
            << "Network/GPU  : " << hw.network << "/" << hw.graphics << "\n"
            << "Compatibility: " << (hw.koronos_compatibility ? "required/unknown" : "native candidate") << "\n";

  page("SOURCE", "Select the staged installation payload. This step only prepares a plan.");
  InstallPlan plan;
  plan.source_root = argc > 1 ? argv[1] : ask("Source payload directory", "/run/chimera/live");
  plan.target_root = argc > 2 ? argv[2] : ask("Target mount directory (preview only)", "/target");
  plan.dry_run = true;

  page("EDITION", "Aurora is the default desktop. Marine is selectable after its staged payload is available.");
  const std::string desktop = ask("Desktop (aurora/marine/none)", "aurora");
  if (desktop != "aurora" && desktop != "marine" && desktop != "none") {
    std::cerr << "Invalid desktop choice; no disk changes were made.\n";
    return 2;
  }
  if (desktop == "none") plan.install_aurora = false;

  page("REVIEW", "Planned operations are shown below. No partitioning, formatting, bootloader writes, or installation will occur.");
  for (const auto& step : installer.build_plan(plan)) {
    std::cout << "  [" << step.id << "] " << step.title << "\n"
              << "      " << step.detail << "\n";
  }
  std::cout << "\nSource: " << plan.source_root << "\nTarget: " << plan.target_root
            << "\nDesktop: " << desktop << "\nFirmware: " << Installer::firmware_name(hw.firmware) << "\n";
  const std::string confirm = ask("Type PREVIEW to print the non-destructive plan", "cancel");
  if (confirm != "PREVIEW") {
    std::cout << "Cancelled. No disk changes were made.\n";
    return 0;
  }

  page("PLAN ONLY", "Production storage and bootloader backends are not implemented yet.");
  const int result = installer.execute(plan, false);
  std::cout << "\n" << muted
            << "This executable is currently a guided text-mode planning frontend, not a graphical installer. "
               "It deliberately cannot erase disks or claim installation success.\n"
            << "Required before production use: transactional partition/filesystem/bootloader backends, "
               "signed payload verification, rollback journal, and BIOS/UEFI install-and-reboot tests.\n"
            << reset;
  return result;
}

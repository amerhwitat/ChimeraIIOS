#include "chimera/installer_core.hpp"
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

std::string choose(const std::string& label, const std::string& choices,
                   const std::string& fallback) {
  std::cout << choices << "\n";
  const std::string value = ask(label, fallback);
  return value;
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
            << "2. Try Live environment (boot-menu action required)\n"
            << "3. Recovery / diagnostics (boot-menu action required)\n"
            << "4. Exit\n";
  if (choose("Choose an option", "", "1") != "1") {
    std::cout << "No disk changes were made. Use the boot menu for Live or Recovery.\n";
    return 0;
  }

  page("HARDWARE", "Detected platform summary; unresolved devices must be reviewed.");
  std::cout << "Architecture : " << hw.architecture << "\n"
            << "CPU vendor   : " << hw.cpu_vendor << "\n"
            << "Logical CPUs : " << hw.cpu_cores << "\n"
            << "Firmware     : " << Installer::firmware_name(hw.firmware) << "\n"
            << "NVMe/SATA    : " << hw.nvme << "/" << hw.sata << "\n"
            << "Network/GPU  : " << hw.network << "/" << hw.graphics << "\n"
            << "Compatibility: " << (hw.koronos_compatibility ? "required/unknown" : "native candidate") << "\n";

  page("LANGUAGE & ACCESSIBILITY", "Keyboard-operable setup with locale and accessibility preferences.");
  InstallPlan plan;
  plan.locale = choose("Locale (e.g. en_US.UTF-8, ar_JO.UTF-8)", "", "en_US.UTF-8");
  plan.keyboard = choose("Keyboard layout (e.g. us, ar)", "", "us");
  const std::string accessibility = choose("Accessibility (none/screen-reader/high-contrast)", "", "none");

  page("DATE, TIME & NETWORK", "Network and time settings are recorded for the plan only.");
  plan.timezone = ask("Timezone", "UTC");
  plan.network_mode = choose("Network mode (offline/dhcp/static/proxy)", "", "dhcp");

  page("INSTALLATION SOURCE", "Choose the verified staged payload directory.");
  plan.source_root = argc > 1 ? argv[1] : ask("Source payload directory", "/run/chimera/live");
  plan.target_root = argc > 2 ? argv[2] : ask("Target mount directory (preview only)", "/target");

  page("DESTINATION & PARTITIONING", "No disks are enumerated or modified by this planning frontend.");
  plan.target_device_id = ask("Stable disk ID (/dev/disk/by-id/...), or UNSELECTED", "UNSELECTED");
  plan.partition_strategy = choose("Partition strategy (guided-erase/manual/alongside)", "", "guided-erase");
  if (plan.partition_strategy != "guided-erase" &&
      plan.partition_strategy != "manual" &&
      plan.partition_strategy != "alongside") {
    std::cerr << "Invalid partition strategy; no disk changes were made.\n";
    return 2;
  }

  page("FILESYSTEM & SECURITY", "Encryption and Secure Boot choices are not applied in preview mode.");
  plan.filesystem = choose("Filesystem (qfs/ext4/btrfs/xfs)", "", "qfs");
  if (plan.filesystem != "qfs" && plan.filesystem != "ext4" &&
      plan.filesystem != "btrfs" && plan.filesystem != "xfs") {
    std::cerr << "Unsupported filesystem selection; no disk changes were made.\n";
    return 2;
  }
  plan.encryption = choose("Encryption (none/luks2)", "", "none");
  if (plan.encryption != "none" && plan.encryption != "luks2") {
    std::cerr << "Invalid encryption choice; no disk changes were made.\n";
    return 2;
  }
  plan.secure_boot = choose("Secure Boot (enable/disable)", "", "disable") == "enable";

  page("EDITION & SOFTWARE", "Only software already present in the signed installation source can be selected.");
  plan.desktop = choose("Desktop (aurora/marine/none)", "", "aurora");
  if (plan.desktop != "aurora" && plan.desktop != "marine" && plan.desktop != "none") {
    std::cerr << "Invalid desktop choice; no disk changes were made.\n";
    return 2;
  }
  plan.install_aurora = plan.desktop == "aurora";
  plan.software_profile = choose("Software profile (minimal/desktop/developer/compatibility)", "", "desktop");
  if (plan.software_profile != "minimal" && plan.software_profile != "desktop" &&
      plan.software_profile != "developer" && plan.software_profile != "compatibility") {
    std::cerr << "Invalid software profile; no disk changes were made.\n";
    return 2;
  }

  page("ACCOUNTS & SYSTEM IDENTITY", "Credentials are deliberately not collected by this preview frontend.");
  plan.hostname = ask("Hostname", "chimera");
  plan.username = ask("Initial user name (name only; no password collected)", "user");
  plan.bootloader = choose("Boot target (spitfire/grub2)", "", "spitfire");
  if (plan.bootloader != "spitfire" && plan.bootloader != "grub2") {
    std::cerr << "Invalid boot target; no disk changes were made.\n";
    return 2;
  }

  page("DRIVERS & TRUST", "Native-first discovery; unknown binaries must remain quarantined.");
  const std::string driver_policy = choose("Driver policy (verified-only/none)", "", "verified-only");
  if (driver_policy != "verified-only" && driver_policy != "none") {
    std::cerr << "Invalid driver policy; no disk changes were made.\n";
    return 2;
  }
  plan.deep_driver_search = driver_policy == "verified-only";
  plan.download_driver_binaries = false;  // Network acquisition is not implemented in this frontend.
  plan.install_detected_drivers = false;  // Never claim installation of unverified driver payloads.
  plan.verify_driver_signatures = true;
  plan.dry_run = true;

  page("FINAL REVIEW", "Review all choices. This frontend cannot erase, partition, format, encrypt, or install a bootloader.");
  for (const auto& step : installer.build_plan(plan)) {
    std::cout << "  [" << step.id << "] " << step.title << "\n"
              << "      " << step.detail << "\n";
  }
  std::cout << "\nLocale: " << plan.locale << " | Keyboard: " << plan.keyboard
            << " | Accessibility: " << accessibility
            << "\nTimezone: " << plan.timezone << " | Network: " << plan.network_mode
            << "\nSource: " << plan.source_root << "\nTarget mount: " << plan.target_root
            << "\nStable disk ID: " << plan.target_device_id
            << "\nPartition strategy: " << plan.partition_strategy
            << "\nFilesystem: " << plan.filesystem << " | Encryption: " << plan.encryption
            << " | Secure Boot: " << (plan.secure_boot ? "enabled" : "disabled")
            << "\nDesktop: " << plan.desktop << " | Software: " << plan.software_profile
            << "\nHostname: " << plan.hostname << " | User: " << plan.username
            << "\nBoot target: " << plan.bootloader << " | Driver policy: " << driver_policy << "\n";

  const std::string confirm = ask("Type PREVIEW to print the non-destructive plan", "cancel");
  if (confirm != "PREVIEW") {
    std::cout << "Cancelled. No disk changes were made.\n";
    return 0;
  }

  page("PLAN ONLY", "Production storage and bootloader backends are not implemented yet.");
  const int result = installer.execute(plan, false);
  std::cout << "\n" << muted
            << "This executable is a guided text-mode planning frontend, not a graphical installer. "
               "It deliberately cannot erase disks or claim installation success.\n"
            << "Required before production use: transactional partition/filesystem/bootloader backends, "
               "signed payload verification, rollback journal, and BIOS/UEFI install-and-reboot tests.\n"
            << reset;
  return result;
}

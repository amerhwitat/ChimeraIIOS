#include "chimera/installer_core.hpp"
#include <iostream>
#include <string>

namespace {
bool ask_yes_no(const std::string& prompt) {
  std::string answer;
  std::cout << prompt << " [y/N] " << std::flush;
  if (!std::getline(std::cin, answer)) return false;
  return answer == "y" || answer == "Y" || answer == "yes" || answer == "YES";
}
std::string ask_text(const std::string& prompt, const std::string& fallback) {
  std::string value;
  std::cout << prompt << " [" << fallback << "]: " << std::flush;
  if (!std::getline(std::cin, value) || value.empty()) return fallback;
  return value;
}
}

int main(int argc, char** argv) {
  using namespace chimera::installer;
  Installer installer;
  const Hardware hw = installer.detect_hardware();

  std::cout << "\nChimera II Setup — keyboard-only text mode\n"
            << "==========================================\n"
            << "Architecture : " << hw.architecture << "\n"
            << "Firmware     : " << Installer::firmware_name(hw.firmware) << "\n"
            << "CPU cores    : " << hw.cpu_cores << "\n"
            << "NVMe/SATA    : " << (hw.nvme ? "yes" : "no") << "/"
            << (hw.sata ? "yes" : "no") << "\n"
            << "Network/GPU  : " << (hw.network ? "detected" : "not detected")
            << "/" << (hw.graphics ? "detected" : "not detected") << "\n\n";

  if (!ask_yes_no("Review the shared installation plan?")) {
    std::cout << "Cancelled; no changes made.\n";
    return 0;
  }

  InstallPlan plan;
  plan.source_root = argc > 1 ? argv[1] : ask_text("Installation source", "/run/chimera/live");
  plan.target_root = argc > 2 ? argv[2] : ask_text("Target root (mounted target only)", "/target");
  plan.locale = ask_text("Installation language / locale", "en_US.UTF-8");
  plan.timezone = ask_text("Time zone (IANA name)", "UTC");
  plan.keyboard_layout = ask_text("Console keyboard layout", "us");
  plan.input_languages = ask_text("Input languages (comma-separated)", "en");
  plan.hardware_clock_utc = ask_yes_no("Keep hardware clock in UTC?");
  plan.enable_ntp = ask_yes_no("Enable network time synchronization?");
  plan.dry_run = true;

  std::cout << "\nPlanned phases (shared Installer::build_plan backend):\n";
  for (const auto& step : installer.build_plan(plan)) {
    std::cout << " - [" << step.id << "] " << step.title << "\n"
              << "     " << step.detail << "\n";
  }
  std::cout << "\nSource: " << plan.source_root << "\nTarget: " << plan.target_root
            << "\nFilesystem: " << plan.filesystem << "\nBootloader: "
            << plan.bootloader << "\n\n";

  const int plan_rc = installer.execute(plan, false);
  if (plan_rc != 0) {
    std::cerr << "PLAN FAILED: backend returned " << plan_rc << ".\n";
    return plan_rc;
  }

  if (!ask_yes_no("Attempt an actual installation now?")) {
    std::cout << "PLAN ONLY: no installation was performed and no success is claimed.\n";
    return 0;
  }

  std::cerr << "\nINSTALLATION BLOCKED: the current backend copies payload files and "
               "writes metadata, but does not implement the required transactional "
               "partition/filesystem/mount, durable journal/rollback, verified-write, "
               "bootloader, and post-install reboot-verification operations.\n"
               "No destructive operation was attempted. Do not interpret this plan as "
               "an installation or as success.\n"
               "Both GUI and text frontends must remain blocked until the shared "
               "transaction backend implements and verifies those operations.\n";
  return 78; // EX_CONFIG: fail closed until a production transaction backend exists.
}

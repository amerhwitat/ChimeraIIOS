#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>
namespace chimera::installer {
enum class Mode { Live, Install, Recovery, Compatibility };
enum class Firmware { BIOS, UEFI, Unknown };
struct Hardware {
  std::string architecture{"x86_64"};
  std::string cpu_vendor{"unknown"};
  uint32_t cpu_cores{1};
  bool koronos_compatibility{false};
  Firmware firmware{Firmware::Unknown};
  bool nvme{false}, sata{false}, network{false}, graphics{false};
};
struct InstallPlan {
  std::filesystem::path target_root;
  std::filesystem::path source_root;
  std::string bootloader{"spitfire"};
  std::string kernel{"koronos"};
  std::string filesystem{"qfs"};
  std::string storage_mode{"guided"};
  std::string edition{"desktop"};
  std::string desktop_profile{"aurora"};
  bool preserve_existing_os{true};
  bool encrypt_root{false};
  std::string locale{"en_US.UTF-8"};
  std::string timezone{"UTC"};
  std::string keyboard_layout{"us"};
  std::string input_languages{"en"};
  bool hardware_clock_utc{true};
  bool enable_ntp{true};
  bool install_aurora{true}, install_kore{true}, install_compatibility{true};
  bool deep_driver_search{true};
  bool download_driver_binaries{true};
  bool install_detected_drivers{true};
  bool verify_driver_signatures{true};
  bool dry_run{true};
};
struct Step { std::string id, title, detail; };
class Installer {
public:
  Hardware detect_hardware() const;
  std::vector<Step> build_plan(const InstallPlan&) const;
  int execute(const InstallPlan&, bool destructive_confirmation);
  static std::string firmware_name(Firmware);
private:
  int copy_tree(const std::filesystem::path&, const std::filesystem::path&) const;
  int run(const std::string&, bool allow_failure=false) const;
};
}

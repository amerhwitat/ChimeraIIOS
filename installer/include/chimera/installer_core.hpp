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
  // Captured by the guided setup planner. These values are not applied until a
  // verified storage/boot transaction backend is available.
  std::string target_device_id{"UNSELECTED"};
  std::string partition_strategy{"guided"};
  std::string encryption{"none"};
  std::string desktop{"aurora"};
  std::string locale{"en_US.UTF-8"};
  std::string keyboard{"us"};
  std::string timezone{"UTC"};
  std::string network_mode{"dhcp"};
  std::string hostname{"chimera"};
  std::string username{"user"};
  std::string software_profile{"desktop"};
  bool secure_boot{false};
  std::string bootloader{"spitfire"};
  std::string kernel{"koronos"};
  std::string filesystem{"qfs"};
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

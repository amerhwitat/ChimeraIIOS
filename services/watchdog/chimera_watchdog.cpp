// Chimera II watchdog service — userspace process supervisor.
//
// Reads `<id> <timeout-ms>` pairs from a config file, watches per-process
// heartbeat files under <root>/heartbeats, and writes a recovery request to
// <root>/recovery when a heartbeat goes stale.
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

namespace fs = std::filesystem;
using chimera_clock = std::chrono::steady_clock;

struct Entry {
  std::string id;
  std::chrono::milliseconds timeout{5000};
};

static uint64_t mono_ns() {
  return static_cast<uint64_t>(
      std::chrono::duration_cast<std::chrono::nanoseconds>(chimera_clock::now().time_since_epoch()).count());
}

static std::vector<Entry> load_config(const fs::path& p) {
  std::vector<Entry> v;
  std::ifstream in(p);
  std::string id;
  uint64_t ms = 0;
  while (in >> id >> ms) {
    if (!id.empty() && ms && ms <= 3600000) v.push_back({id, std::chrono::milliseconds(ms)});
  }
  return v;
}

// Write a heartbeat atomically (tmp + rename) so readers never see a partial file.
static void heartbeat(const fs::path& root, const std::string& id) {
  if (id.empty()) return;
  auto d = root / "heartbeats";
  fs::create_directories(d);
  auto tmp = d / (id + ".hb.tmp"), dst = d / (id + ".hb");
  std::ofstream o(tmp, std::ios::trunc);
  o << mono_ns() << "\n";
  o.close();
  std::error_code ec;
  fs::rename(tmp, dst, ec);
  if (ec) fs::remove(tmp, ec);
}

static void recovery(const fs::path& d, const Entry& e, uint64_t now, uint64_t age) {
  fs::create_directories(d);
  auto tmp = d / (e.id + ".request.tmp"), dst = d / (e.id + ".request");
  std::ofstream o(tmp);
  o << e.id << " " << age << " " << now << "\n";
  o.close();
  std::error_code ec;
  fs::rename(tmp, dst, ec);
  if (ec) fs::remove(tmp, ec);
}

int main(int argc, char** argv) {
  fs::path config = "/etc/chimera/watchdog.conf", root = "/run/chimera/watchdog";
  uint64_t interval = 1000;
  std::string heartbeat_id;
  for (int i = 1; i < argc; ++i) {
    std::string a = argv[i];
    if (a == "--config" && i + 1 < argc) config = argv[++i];
    else if (a == "--root" && i + 1 < argc) root = argv[++i];
    else if (a == "--interval-ms" && i + 1 < argc) interval = std::strtoull(argv[++i], nullptr, 10);
    else if (a == "--heartbeat" && i + 1 < argc) heartbeat_id = argv[++i];
    else if (a == "--help") {
      std::cout << "chimera-watchdog [--config PATH] [--root PATH] [--interval-ms N] [--heartbeat ID]\n";
      return 0;
    } else {
      return 2;
    }
  }
  auto entries = load_config(config);
  if (entries.empty()) return 3;
  auto hb = root / "heartbeats", rec = root / "recovery";
  fs::create_directories(hb);
  fs::create_directories(rec);
  std::cout << "[WDOG] Chimera watchdog online; entries=" << entries.size() << "\n";
  for (;;) {
    // Refresh our own heartbeat before sampling the clock, otherwise the stamp we
    // just wrote can be newer than `now` and would look infinitely stale.
    if (!heartbeat_id.empty()) heartbeat(root, heartbeat_id);
    uint64_t now = mono_ns();
    for (const auto& e : entries) {
      auto hp = hb / (e.id + ".hb");
      if (!fs::exists(hp)) continue;
      std::ifstream in(hp);
      uint64_t stamp = 0;
      if (in) in >> stamp;
      uint64_t timeout = static_cast<uint64_t>(e.timeout.count()) * 1000000ull;
      // A stamp newer than `now` means a concurrent heartbeat write: treat as fresh.
      uint64_t age = stamp ? (now >= stamp ? now - stamp : 0) : UINT64_MAX;
      if (age >= timeout) {
        recovery(rec, e, now, age);
      } else {
        std::error_code ec;
        fs::remove(rec / (e.id + ".request"), ec);
      }
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(interval ? interval : 1000));
  }
}

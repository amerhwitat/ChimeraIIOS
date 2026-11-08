#include <cerrno>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <string>
#if defined(_WIN32)
#include <windows.h>
#include <process.h>
#else
#include <sys/utsname.h>
#include <unistd.h>
#endif
#include <utility>
#include <vector>

namespace fs = std::filesystem;

static void usage()
{
    std::cout << "chmctl: status | settings [ARGS...] | services | devices | network | logs | reboot | shutdown | help\n";
}

static int exec_tool(const std::string& tool, std::vector<std::string> args)
{
    std::vector<char*> argv;
    argv.reserve(args.size() + 1);
    for (auto& arg : args) argv.push_back(arg.data());
    argv.push_back(nullptr);
#if defined(_WIN32)
    const int spawn_result = _spawnvp(_P_WAIT, tool.c_str(), argv.data());
    if (spawn_result >= 0) return spawn_result;
#else
    execvp(tool.c_str(), argv.data());
#endif
    const int saved = errno;
    std::cerr << "chmctl: provider '" << tool << "' unavailable: " << std::strerror(saved) << "\n";
    return saved == ENOENT ? 127 : 126;
}

static int status()
{
#if defined(_WIN32)
    OSVERSIONINFOA version{};
    version.dwOSVersionInfoSize = sizeof(version);
    SYSTEM_INFO system_info{};
    GetNativeSystemInfo(&system_info);
    char host[256] = "unknown";
    DWORD host_size = static_cast<DWORD>(sizeof(host));
    if (GetVersionExA(&version))
        std::cout << "Kernel: Windows NT " << version.dwMajorVersion << "." << version.dwMinorVersion << "\n";
    else
        std::cout << "Kernel: Windows NT (version unavailable)\n";
    if (GetComputerNameA(host, &host_size))
        std::cout << "Hostname: " << host << "\n";
    else
        std::cout << "Hostname: unavailable\n";
    const char* architecture = "unknown";
    switch (system_info.wProcessorArchitecture) {
        case PROCESSOR_ARCHITECTURE_AMD64: architecture = "x86_64"; break;
        case PROCESSOR_ARCHITECTURE_ARM64: architecture = "aarch64"; break;
        case PROCESSOR_ARCHITECTURE_INTEL: architecture = "i686"; break;
        case PROCESSOR_ARCHITECTURE_ARM: architecture = "arm"; break;
        default: break;
    }
    std::cout << "Architecture: " << architecture << "\n";
#else
    struct utsname u{};
    char host[256] = "unknown";
    if (uname(&u) == 0)
        std::cout << "Kernel: " << u.sysname << " " << u.release << " (" << u.machine << ")\n";
    else
        std::cout << "Kernel: unavailable (" << std::strerror(errno) << ")\n";
    if (gethostname(host, sizeof(host) - 1) == 0)
        std::cout << "Hostname: " << host << "\n";
    else
        std::cout << "Hostname: unavailable\n";
#endif
    for (const char* state : {"/run/kore/state.json", "/run/spotnik/state.json", "/run/aegis/state.json"}) {
        std::cout << state << ": " << (fs::is_regular_file(state) ? "present" : "not-present") << "\n";
    }
    std::cout << "This is a live status probe; it does not infer that services or drivers are operational.\n";
    return 0;
}

int main(int argc, char** argv)
{
    if (argc < 2) { usage(); return 2; }
    const std::string command = argv[1];
    if (command == "status") return status();
    if (command == "help" || command == "--help" || command == "-h") { usage(); return 0; }
    if (command == "settings") {
        std::vector<std::string> args{"aurora-settings"};
        if (argc == 2) args.emplace_back("list");
        for (int i = 2; i < argc; ++i) args.emplace_back(argv[i]);
        return exec_tool("aurora-settings", std::move(args));
    }
    if (command == "services") return exec_tool("korectl", {"korectl", "list"});
    if (command == "devices") return exec_tool("aurora-peripherals", {"aurora-peripherals", "list"});
    if (command == "network") return exec_tool("ip", {"ip", "-brief", "address"});
    if (command == "logs") return exec_tool("dmesg", {"dmesg"});
    if (command == "reboot") return exec_tool("korectl", {"korectl", "reboot"});
    if (command == "shutdown") return exec_tool("korectl", {"korectl", "shutdown"});
    usage();
    return 127;
}

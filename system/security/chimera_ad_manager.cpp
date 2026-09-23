#include "chimera_identity_store.hpp"
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <netdb.h>
#include <sstream>
#include <string>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

using namespace chimera_identity;

static bool command_exists(const char* name) {
    const char* path = std::getenv("PATH");
    if (!path) {
        return false;
    }

    std::stringstream dirs(path);
    std::string dir;
    while (std::getline(dirs, dir, ':')) {
        if (access((dir + "/" + name).c_str(), X_OK) == 0) {
            return true;
        }
    }
    return false;
}

static int run_tool(const char* program, const std::vector<std::string>& args) {
    pid_t pid = fork();
    if (pid < 0) {
        return 1;
    }

    if (pid == 0) {
        std::vector<char*> argv;
        argv.reserve(args.size() + 2);
        argv.push_back(const_cast<char*>(program));

        for (const auto& arg : args) {
            argv.push_back(const_cast<char*>(arg.c_str()));
        }

        argv.push_back(nullptr);
        execvp(program, argv.data());
        _exit(127);
    }

    int status = 0;
    if (waitpid(pid, &status, 0) < 0) {
        return 1;
    }

    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}

static std::string provider_nss_module(const std::string& provider) {
    return provider == "sssd" ? "sss" : "winbind";
}

static std::string provider_pam_module(const std::string& provider) {
    return provider == "sssd" ? "pam_sss.so" : "pam_winbind.so";
}

static int configure() {
    if (!privileged() || !ensure_db()) {
        return 77;
    }

    std::string domain;
    std::string realm;
    std::string dc;
    std::string provider;

    std::cerr << "AD DNS domain: ";
    std::getline(std::cin, domain);

    if (!valid_name(domain) && domain.find('.') == std::string::npos) {
        return 2;
    }

    std::cerr << "Kerberos realm [uppercase domain]: ";
    std::getline(std::cin, realm);

    if (realm.empty()) {
        realm = domain;
        for (char& c : realm) {
            c = static_cast<char>(
                std::toupper(static_cast<unsigned char>(c))
            );
        }
    }

    std::cerr << "Domain controller (optional): ";
    std::getline(std::cin, dc);

    std::cerr << "Provider [sssd/winbind]: ";
    std::getline(std::cin, provider);

    if (provider.empty()) {
        provider = "sssd";
    }

    if (provider != "sssd" && provider != "winbind") {
        return 2;
    }

    const std::string kdc = dc.empty() ? domain : dc;

    std::string krb;
    krb += "[libdefaults]\n";
    krb += " default_realm = " + realm + "\n";
    krb += " rdns = false\n";
    krb += " dns_lookup_kdc = true\n";
    krb += "\n";
    krb += "[realms]\n";
    krb += " " + realm + " = {\n";
    krb += "  kdc = " + kdc + "\n";
    krb += " }\n";

    std::string nss;
    read_all(root() / "etc/nsswitch.conf", nss);

    if (nss.empty()) {
        nss = "passwd: files\n"
              "group: files\n"
              "shadow: files\n";
    }

    const std::string nss_module = provider_nss_module(provider);

    std::istringstream nss_input(nss);
    std::string line;
    std::string nss_output;
    bool passwd_found = false;
    bool group_found = false;

    while (std::getline(nss_input, line)) {
        if (line.rfind("passwd:", 0) == 0) {
            line = "passwd: files " + nss_module;
            passwd_found = true;
        } else if (line.rfind("group:", 0) == 0) {
            line = "group: files " + nss_module;
            group_found = true;
        }

        nss_output += line;
        nss_output += '\n';
    }

    if (!passwd_found) {
        nss_output += "passwd: files " + nss_module + "\n";
    }

    if (!group_found) {
        nss_output += "group: files " + nss_module + "\n";
    }

    nss = std::move(nss_output);

    const std::string pam_module = provider_pam_module(provider);

    std::string pam;
    pam += "# Chimera II domain authentication\n";
    pam += "auth required " + pam_module + "\n";
    pam += "account required " + pam_module + "\n";

    std::string summary;
    summary += "{\n";
    summary += "  \"enabled\": true,\n";
    summary += "  \"domain\": \"" + domain + "\",\n";
    summary += "  \"realm\": \"" + realm + "\",\n";
    summary += "  \"provider\": \"" + provider + "\",\n";
    summary += "  \"controller\": \"" + dc + "\",\n";
    summary += "  \"credentials\": \"never stored\"\n";
    summary += "}\n";

    const bool written =
        atomic_write(root() / "etc/krb5.conf", krb, 0644) &&
        atomic_write(root() / "etc/nsswitch.conf", nss, 0644) &&
        atomic_write(root() / "etc/pam.d/chimera-domain", pam, 0644) &&
        atomic_write(root() / "etc/chimera/ad.conf", summary, 0640);

    if (!written) {
        return 1;
    }

    std::cout << "AD configuration staged for "
              << domain
              << " using "
              << provider
              << "\n";

    return 0;
}

static int join() {
    if (!privileged()) {
        return 77;
    }

    std::string domain;
    std::string user;
    std::string provider;

    std::cerr << "AD DNS domain: ";
    std::getline(std::cin, domain);

    std::cerr << "Join user: ";
    std::getline(std::cin, user);

    std::cerr << "Provider [sssd/winbind]: ";
    std::getline(std::cin, provider);

    if (provider.empty()) {
        provider = "sssd";
    }

    if (provider != "sssd" && provider != "winbind") {
        return 2;
    }

    std::cerr
        << "Credentials will be collected by the provider; continue? [yes/no]: ";

    std::string confirmation;
    std::getline(std::cin, confirmation);

    if (confirmation != "yes") {
        return 1;
    }

    if (provider == "sssd" && command_exists("realm")) {
        return run_tool("realm", {"join", "--user=" + user, domain});
    }

    if (provider == "winbind" && command_exists("net")) {
        return run_tool("net", {"ads", "join", "-U", user});
    }

    std::cerr << "No supported AD join provider is installed.\n";
    return 78;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout
            << "usage: chm-ad status|config|configure|join|leave|test|users|groups\n";
        return 2;
    }

    const std::string operation = argv[1];

    if (operation == "status") {
        std::cout << "Providers: "
                  << (command_exists("realm") ? "realmd " : "")
                  << (command_exists("sssd") ? "sssd " : "")
                  << (command_exists("winbindd") ? "winbind " : "")
                  << "\n";
        return 0;
    }

    if (operation == "config") {
        std::ifstream file(root() / "etc/chimera/ad.conf");
        std::cout << file.rdbuf();
        return file ? 0 : 1;
    }

    if (operation == "configure") {
        return configure();
    }

    if (operation == "join") {
        return join();
    }

    if (operation == "leave") {
        std::cerr
            << "Use realm leave or net ads leave after explicit administrator confirmation.\n";
        return 78;
    }

    if (operation == "test") {
        std::string dns_name;
        std::cerr << "DNS name: ";
        std::getline(std::cin, dns_name);

        addrinfo* result = nullptr;
        const int rc = getaddrinfo(dns_name.c_str(), nullptr, nullptr, &result);

        if (result) {
            freeaddrinfo(result);
        }

        return rc ? 1 : 0;
    }

    if (operation == "users" || operation == "groups") {
        std::cout
            << "Enumeration is provided through configured NSS/SSSD/winbind integration.\n";
        return 0;
    }

    return 2;
}

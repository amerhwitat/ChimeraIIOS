#include <arpa/inet.h>
#include <cassert>
#include <cstring>
#include <string>

int main() {
    assert(chimera_ntohs(chimera_htons(0x1234)) == 0x1234);
    assert(chimera_ntohl(chimera_htonl(0x12345678u)) == 0x12345678u);

    struct in_addr v4{};
    assert(chimera_inet_pton(AF_INET, "192.0.2.1", &v4) == 1);
    char text4[INET_ADDRSTRLEN]{};
    assert(chimera_inet_ntop(AF_INET, &v4, text4, sizeof(text4)) != nullptr);
    assert(std::string(text4) == "192.0.2.1");
    assert(chimera_inet_aton("192.0.2.1", &v4) == 1);
    assert(chimera_inet_ntohl(v4.s_addr) == 0xC0000201u);

    struct in6_addr v6{};
    assert(chimera_inet_pton(AF_INET6, "2001:db8::1", &v6) == 1);
    char text6[INET6_ADDRSTRLEN]{};
    assert(chimera_inet_ntop(AF_INET6, &v6, text6, sizeof(text6)) != nullptr);
    assert(std::string(text6) == "2001:db8::1");

    assert(chimera_inet_pton(AF_INET, "999.1.1.1", &v4) == 0);
    assert(chimera_inet_pton(AF_INET6, "2001:::1", &v6) == 0);
    assert(chimera_inet_pton(12345, "192.0.2.1", &v4) == -1);

    return 0;
}

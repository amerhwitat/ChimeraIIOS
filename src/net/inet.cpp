#include <arpa/inet.h>

#include <array>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <string>
#include <string_view>
#include <vector>

namespace {
uint16_t swap16(uint16_t v) { return static_cast<uint16_t>((v << 8) | (v >> 8)); }
uint32_t swap32(uint32_t v) {
    return ((v & 0x000000FFu) << 24) | ((v & 0x0000FF00u) << 8) |
           ((v & 0x00FF0000u) >> 8) | ((v & 0xFF000000u) >> 24);
}
uint16_t host_to_net16(uint16_t v) {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return swap16(v);
#else
    return v;
#endif
}
uint32_t host_to_net32(uint32_t v) {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return swap32(v);
#else
    return v;
#endif
}

bool parse_ipv4(std::string_view s, std::array<uint8_t, 4>& out) {
    size_t pos = 0;
    for (size_t i = 0; i < 4; ++i) {
        if (pos >= s.size()) return false;
        size_t end = s.find('.', pos);
        if (i == 3) end = s.size();
        if (end == pos || end > s.size()) return false;
        unsigned value = 0;
        for (size_t j = pos; j < end; ++j) {
            unsigned char c = static_cast<unsigned char>(s[j]);
            if (!std::isdigit(c)) return false;
            value = value * 10u + static_cast<unsigned>(c - '0');
            if (value > 255u) return false;
        }
        out[i] = static_cast<uint8_t>(value);
        if (i < 3) {
            if (end == s.size() || s[end] != '.') return false;
            pos = end + 1;
        }
    }
    return pos == s.size();
}

bool parse_hex16(std::string_view s, uint16_t& value) {
    if (s.empty() || s.size() > 4) return false;
    unsigned v = 0;
    for (char c : s) {
        unsigned d;
        if (c >= '0' && c <= '9') d = static_cast<unsigned>(c - '0');
        else if (c >= 'a' && c <= 'f') d = static_cast<unsigned>(c - 'a' + 10);
        else if (c >= 'A' && c <= 'F') d = static_cast<unsigned>(c - 'A' + 10);
        else return false;
        v = (v << 4) | d;
    }
    value = static_cast<uint16_t>(v);
    return true;
}

bool parse_ipv6_side(std::string_view side, std::vector<uint16_t>& words) {
    if (side.empty()) return true;
    size_t pos = 0;
    while (pos < side.size()) {
        size_t end = side.find(':', pos);
        if (end == std::string_view::npos) end = side.size();
        auto token = side.substr(pos, end - pos);
        if (token.empty()) return false;
        if (token.find('.') != std::string_view::npos) {
            if (end != side.size()) return false;
            std::array<uint8_t, 4> v4{};
            if (!parse_ipv4(token, v4)) return false;
            words.push_back(static_cast<uint16_t>((v4[0] << 8) | v4[1]));
            words.push_back(static_cast<uint16_t>((v4[2] << 8) | v4[3]));
        } else {
            uint16_t value = 0;
            if (!parse_hex16(token, value)) return false;
            words.push_back(value);
        }
        if (words.size() > 8) return false;
        pos = end;
        if (pos < side.size()) ++pos;
    }
    return true;
}

bool parse_ipv6(std::string_view s, std::array<uint8_t, 16>& out) {
    if (s.empty()) return false;
    size_t dc = s.find("::");
    if (dc != std::string_view::npos && s.find("::", dc + 2) != std::string_view::npos) return false;
    std::vector<uint16_t> left, right;
    if (dc == std::string_view::npos) {
        if (!parse_ipv6_side(s, left) || left.size() != 8) return false;
    } else {
        if (!parse_ipv6_side(s.substr(0, dc), left) || !parse_ipv6_side(s.substr(dc + 2), right)) return false;
        if (left.size() + right.size() >= 8) return false;
    }
    std::array<uint16_t, 8> words{};
    size_t at = 0;
    for (uint16_t v : left) words[at++] = v;
    if (dc != std::string_view::npos) at = 8 - right.size();
    for (uint16_t v : right) words[at++] = v;
    for (size_t i = 0; i < 8; ++i) {
        out[2*i] = static_cast<uint8_t>(words[i] >> 8);
        out[2*i + 1] = static_cast<uint8_t>(words[i]);
    }
    return true;
}

std::string format_ipv6(const uint8_t* p) {
    uint16_t w[8]{};
    for (size_t i = 0; i < 8; ++i) w[i] = static_cast<uint16_t>((p[2*i] << 8) | p[2*i+1]);
    size_t best_start = 8, best_len = 0;
    for (size_t i = 0; i < 8;) {
        if (w[i] != 0) { ++i; continue; }
        size_t j = i; while (j < 8 && w[j] == 0) ++j;
        if (j - i > best_len && j - i >= 2) { best_start = i; best_len = j - i; }
        i = j;
    }
    std::string r;
    for (size_t i = 0; i < 8;) {
        if (i == best_start) {
            r += "::";
            i += best_len;
            if (i == 8) break;
        } else {
            if (!r.empty() && r.back() != ':') r += ':';
            char buf[5]; std::snprintf(buf, sizeof(buf), "%x", w[i]); r += buf;
            ++i;
        }
    }
    return r;
}
}

extern "C" uint16_t chimera_htons(uint16_t v) { return host_to_net16(v); }
extern "C" uint16_t chimera_ntohs(uint16_t v) { return host_to_net16(v); }
extern "C" uint32_t chimera_htonl(uint32_t v) { return host_to_net32(v); }
extern "C" uint32_t chimera_ntohl(uint32_t v) { return host_to_net32(v); }

extern "C" int chimera_inet_pton(int af, const char* src, void* dst) {
    if (!src || !dst) return -1;
    if (af == AF_INET) {
        std::array<uint8_t, 4> bytes{};
        if (!parse_ipv4(src, bytes)) return 0;
        std::memcpy(dst, bytes.data(), bytes.size());
        return 1;
    }
    if (af == AF_INET6) {
        std::array<uint8_t, 16> bytes{};
        if (!parse_ipv6(src, bytes)) return 0;
        std::memcpy(dst, bytes.data(), bytes.size());
        return 1;
    }
    return -1;
}

extern "C" const char* chimera_inet_ntop(int af, const void* src, char* dst, size_t size) {
    if (!src || !dst || size == 0) return nullptr;
    if (af == AF_INET) {
        const auto* p = static_cast<const uint8_t*>(src);
        int n = std::snprintf(dst, size, "%u.%u.%u.%u", p[0], p[1], p[2], p[3]);
        return n >= 0 && static_cast<size_t>(n) < size ? dst : nullptr;
    }
    if (af == AF_INET6) {
        std::string s = format_ipv6(static_cast<const uint8_t*>(src));
        if (s.size() + 1 > size) return nullptr;
        std::memcpy(dst, s.c_str(), s.size() + 1);
        return dst;
    }
    return nullptr;
}

extern "C" int chimera_inet_aton(const char* cp, struct in_addr* inp) {
    if (!cp || !inp) return 0;
    std::array<uint8_t, 4> bytes{};
    if (!parse_ipv4(cp, bytes)) return 0;
    uint32_t value = (static_cast<uint32_t>(bytes[0]) << 24) |
                     (static_cast<uint32_t>(bytes[1]) << 16) |
                     (static_cast<uint32_t>(bytes[2]) << 8) | bytes[3];
    inp->s_addr = value;
    return 1;
}

extern "C" uint32_t chimera_inet_addr(const char* cp) {
    struct in_addr addr{};
    return chimera_inet_aton(cp, &addr) ? addr.s_addr : INADDR_NONE;
}

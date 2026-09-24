// Chimera VoiceConnect: clean-room, DirectX-independent voice transport.
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>

namespace chm::voiceconnect {
struct FrameHeader {
    uint32_t magic = 0x43484D56;
    uint16_t version = 1;
    uint16_t codec = 1;
    uint32_t sequence = 0;
    uint32_t sample_rate = 48000;
    uint16_t channels = 1;
    uint16_t samples = 0;
};

class Session {
    int fd_ = -1;
    uint16_t port_;

public:
    explicit Session(uint16_t p) : port_(p) {}
    ~Session() { close(); }

    bool bind() {
        fd_ = ::socket(AF_INET, SOCK_DGRAM, 0);
        if (fd_ < 0) return false;

        int reuse = 1;
        setsockopt(fd_, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

        sockaddr_in a{};
        a.sin_family = AF_INET;
        a.sin_addr.s_addr = htonl(INADDR_ANY);
        a.sin_port = htons(port_);
        return ::bind(fd_, reinterpret_cast<sockaddr*>(&a), sizeof(a)) == 0;
    }

    bool send(const std::string& host, uint16_t port, const int16_t* pcm, uint16_t samples, uint32_t seq) {
        if (fd_ < 0 || !pcm || !samples || samples > 960) {
            return false;
        }

        FrameHeader h{};
        h.sequence = seq;
        h.samples = samples;

        sockaddr_in d{};
        d.sin_family = AF_INET;
        d.sin_port = htons(port);
        if (::inet_pton(AF_INET, host.c_str(), &d.sin_addr) != 1) {
            return false;
        }

        uint8_t packet[sizeof(FrameHeader) + 960 * sizeof(int16_t)]{};
        std::memcpy(packet, &h, sizeof(h));
        std::memcpy(packet + sizeof(h), pcm, samples * sizeof(int16_t));

        return ::sendto(
            fd_, packet, sizeof(h) + samples * sizeof(int16_t), 0,
            reinterpret_cast<sockaddr*>(&d), sizeof(d)) >= 0;
    }

    int receive(int16_t* pcm, uint16_t capacity, FrameHeader& h) {
        uint8_t packet[sizeof(FrameHeader) + 960 * sizeof(int16_t)]{};
        sockaddr_in s{};
        socklen_t n = sizeof(s);

        const auto got = ::recvfrom(
            fd_, packet, sizeof(packet), 0,
            reinterpret_cast<sockaddr*>(&s), &n);

        if (got < static_cast<ssize_t>(sizeof(FrameHeader))) {
            return -1;
        }

        std::memcpy(&h, packet, sizeof(h));
        if (h.magic != 0x43484D56 || h.version != 1 || h.codec != 1 ||
            h.samples > capacity ||
            static_cast<size_t>(got) < sizeof(h) + h.samples * sizeof(int16_t)) {
            return -1;
        }

        std::memcpy(pcm, packet + sizeof(h), h.samples * sizeof(int16_t));
        return h.samples;
    }

    void close() {
        if (fd_ >= 0) {
            ::close(fd_);
            fd_ = -1;
        }
    }
};
}

int main(int argc, char** argv) {
    const uint16_t port = argc > 1 ? static_cast<uint16_t>(std::stoi(argv[1])) : 43000;
    chm::voiceconnect::Session session(port);

    if (!session.bind()) {
        std::cerr << "voiceconnect: bind failed: " << std::strerror(errno) << "\n";
        return 1;
    }

    std::cout << "Chimera VoiceConnect listening on UDP/" << port
              << " (DirectX-independent PCM16 transport)\n";
    std::cout << "Audio adapters are external to the transport.\n";
    return 0;
}

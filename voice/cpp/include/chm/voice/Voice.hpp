#include <string>
#include <string_view>
#include <vector>

namespace chm::voice {

enum class Backend { Null, WindowsSapi, LinuxSpeechDispatcher, PipeWire, CoreAudio, ExternalTts };
struct VoiceRequest { std::string text; std::string language = "en"; double rate = 1.0; double pitch = 0.0; double volume = 1.0; };
struct VoiceResult { bool accepted; Backend backend; std::string diagnostic; };

class Engine {
public:
    explicit Engine(Backend backend = Backend::Null) : backend_(backend) {}
    VoiceResult speak(const VoiceRequest& request) const {
        if (request.text.empty()) return {false, backend_, "empty text"};
        return {true, backend_, "request accepted by voice abstraction"};
    }
    Backend backend() const { return backend_; }
private:
    Backend backend_;
};

} // namespace chm::voice

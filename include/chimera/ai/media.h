#pragma once
#include <string>
#include <string_view>
#include <vector>

namespace chimera::ai::media {
enum class SpeechProvider { Whisper, Vosk };
enum class VisionAlgorithm { Face, Object, Pose, Gesture, OCR, Segmentation, Tracking, Edges };
struct VoiceCommand { std::string text; std::string action; bool requires_confirmation{true}; };
struct AudioFrame { std::vector<std::int16_t> samples; unsigned sample_rate{16000}; unsigned channels{1}; };
struct CameraFrame { unsigned width{}; unsigned height{}; unsigned channels{}; };
VoiceCommand parse_voice_command(std::string_view text);
}

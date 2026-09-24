#pragma once
#include <cstdint>
#include <vector>
namespace chimera::security {
enum class BiometricKind : std::uint8_t { Fingerprint, Face, Iris, Palm, HandGeometry, Voice, Vein, Fido2, SmartCard };
struct BiometricMethod { BiometricKind kind; const char* id; const char* label; bool requires_sensor; bool supported_by_host; bool enrolled; bool enabled; bool liveness_required; };
struct BiometricPolicy { bool allow_password_fallback{true}; bool require_password_for_enrollment{true}; bool require_liveness_for_face{true}; bool allow_remote_biometric_auth{false}; bool require_secure_hardware{false}; };
class BiometricRegistry {
public: BiometricRegistry(); const std::vector<BiometricMethod>& methods() const noexcept{return methods_;}
bool set_enabled(BiometricKind kind,bool enabled) noexcept; bool set_enrolled(BiometricKind kind,bool enrolled) noexcept; const BiometricPolicy& policy() const noexcept{return policy_;}
private: std::vector<BiometricMethod> methods_; BiometricPolicy policy_{};
};
}
// Security and compositor-capture regression tests for ChimeraIIOS / OctavianOS.
// The adapter is deliberately a user-space policy component; integration with the
// kernel IPC broker and compositor must be proven separately by runtime tests.
#include <openssl/evp.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace chimera::security {
enum class Permission : uint32_t {
  none = 0, desktop_read = 1u << 0, desktop_capture = 1u << 1,
  tensor_execute = 1u << 2, neural_inference = 1u << 3,
  system_admin = 1u << 4
};
inline Permission operator|(Permission a, Permission b) {
  return static_cast<Permission>(static_cast<uint32_t>(a) | static_cast<uint32_t>(b));
}
inline bool has_permission(Permission actual, Permission required) {
  const auto a = static_cast<uint32_t>(actual), r = static_cast<uint32_t>(required);
  return (a & r) == r;
}
struct CapabilityToken {
  uint64_t id, session_id;
  Permission permissions;
  uint64_t expires_at_epoch;
  bool revoked;
};
class IPCSecurityManager {
 public:
  uint64_t issue_token(uint64_t session, Permission permissions, uint64_t expires_at) {
    if (session == 0 || permissions == Permission::none || expires_at == 0) return 0;
    const uint64_t id = next_id_++;
    tokens_.emplace(id, CapabilityToken{id, session, permissions, expires_at, false});
    return id;
  }
  bool revoke_token(uint64_t id) {
    auto it = tokens_.find(id);
    if (it == tokens_.end() || it->second.revoked) return false;
    it->second.revoked = true;
    revoked_.insert(id);
    return true;
  }
  bool validate_access(uint64_t id, uint64_t caller_session, Permission required,
                       uint64_t now_epoch) const {
    const auto it = tokens_.find(id);
    if (id == 0 || caller_session == 0 || required == Permission::none ||
        it == tokens_.end() || revoked_.count(id)) return false;
    const auto& t = it->second;
    return !t.revoked && t.session_id == caller_session &&
           now_epoch < t.expires_at_epoch && has_permission(t.permissions, required);
  }
 private:
  std::unordered_map<uint64_t, CapabilityToken> tokens_;
  std::unordered_set<uint64_t> revoked_;
  uint64_t next_id_ = 1000;
};
enum WindowFlag : uint32_t { secure_window = 1u << 0, sensitive_input = 1u << 1 };
struct FrameBufferHeader {
  uint32_t width, height, stride, format;
  size_t payload_size;
  uint32_t security_flags;
};
class CompositorCapturePolicy {
 public:
  CompositorCapturePolicy(bool consent, bool indicator)
      : consent_(consent), indicator_(indicator) {}
  bool authorize_capture(const FrameBufferHeader& h, uint64_t token, uint64_t session,
                         const IPCSecurityManager& manager, uint64_t now) const {
    if (!manager.validate_access(token, session, Permission::desktop_capture, now)) return false;
    if (!consent_ || !indicator_ || h.width == 0 || h.height == 0 || h.format == 0) return false;
    if (h.security_flags & (secure_window | sensitive_input)) return false;
    const uint64_t min_stride = static_cast<uint64_t>(h.width) * 4u;
    if (min_stride > std::numeric_limits<uint32_t>::max() || h.stride < min_stride) return false;
    if (h.height != 0 && static_cast<uint64_t>(h.stride) >
        std::numeric_limits<size_t>::max() / static_cast<size_t>(h.height)) return false;
    const size_t required = static_cast<size_t>(h.stride) * static_cast<size_t>(h.height);
    return h.payload_size >= required;
  }
 private:
  bool consent_, indicator_;
};
inline bool sha256_hex(const std::vector<uint8_t>& bytes, std::string& out) {
  std::array<unsigned char, EVP_MAX_MD_SIZE> digest{};
  unsigned int length = 0;
  EVP_MD_CTX* ctx = EVP_MD_CTX_new();
  if (!ctx) return false;
  const bool ok = EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) == 1 &&
      EVP_DigestUpdate(ctx, bytes.data(), bytes.size()) == 1 &&
      EVP_DigestFinal_ex(ctx, digest.data(), &length) == 1 && length == 32;
  EVP_MD_CTX_free(ctx);
  if (!ok) return false;
  static constexpr char hex[] = "0123456789abcdef";
  out.clear();
  for (unsigned int i = 0; i < length; ++i) {
    out.push_back(hex[digest[i] >> 4]); out.push_back(hex[digest[i] & 0x0f]);
  }
  return true;
}
class ModelAdapterRegistry {
 public:
  bool register_trusted_model(const std::string& id, const std::string& hash) {
    if (id.empty() || hash.size() != 64) return false;
    for (char c : hash) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
    manifest_[id] = hash; return true;
  }
  bool load_and_verify_model(const std::string& id, const std::vector<uint8_t>& bytes) {
    const auto it = manifest_.find(id);
    if (it == manifest_.end()) return false;
    std::string actual;
    if (!sha256_hex(bytes, actual) || actual != it->second) return false;
    loaded_[id] = bytes; return true;
  }
  const std::vector<uint8_t>* get_model(const std::string& id) const {
    const auto it = loaded_.find(id);
    return it == loaded_.end() ? nullptr : &it->second;
  }
 private:
  std::unordered_map<std::string, std::string> manifest_;
  std::unordered_map<std::string, std::vector<uint8_t>> loaded_;
};
}  // namespace chimera::security

int main() {
  using namespace chimera::security;
  int failures = 0;
  const auto check = [&failures](const char* name, bool ok) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << '\n';
    if (!ok) ++failures;
  };
  IPCSecurityManager manager;
  const auto capture = Permission::desktop_capture;
  const uint64_t token = manager.issue_token(501, capture | Permission::tensor_execute, 20000);
  check("valid token", manager.validate_access(token, 501, capture, 1000));
  check("session isolation", !manager.validate_access(token, 502, capture, 1000));
  check("expiry boundary", !manager.validate_access(token, 501, capture, 20000));
  check("least privilege", !manager.validate_access(token, 501, Permission::system_admin, 1000));
  check("revoke once", manager.revoke_token(token) && !manager.validate_access(token, 501, capture, 1000));
  check("no double revoke", !manager.revoke_token(token));

  const uint64_t fresh = manager.issue_token(502, capture, 20000);
  const FrameBufferHeader normal{1920, 1080, 7680, 1, 7680u * 1080u, 0};
  const FrameBufferHeader secure{1920, 1080, 7680, 1, 7680u * 1080u, secure_window};
  const FrameBufferHeader sensitive{1920, 1080, 7680, 1, 7680u * 1080u, sensitive_input};
  const FrameBufferHeader short_payload{1920, 1080, 7680, 1, 12, 0};
  const FrameBufferHeader short_stride{1920, 1080, 32, 1, 32u * 1080u, 0};
  const CompositorCapturePolicy policy(true, true);
  check("ordinary capture with consent and indicator",
        policy.authorize_capture(normal, fresh, 502, manager, 1000));
  check("secure window denied", !policy.authorize_capture(secure, fresh, 502, manager, 1000));
  check("sensitive-input frame denied", !policy.authorize_capture(sensitive, fresh, 502, manager, 1000));
  check("undersized payload denied", !policy.authorize_capture(short_payload, fresh, 502, manager, 1000));
  check("invalid stride denied", !policy.authorize_capture(short_stride, fresh, 502, manager, 1000));
  check("missing consent denied",
        !CompositorCapturePolicy(false, true).authorize_capture(normal, fresh, 502, manager, 1000));
  check("missing indicator denied",
        !CompositorCapturePolicy(true, false).authorize_capture(normal, fresh, 502, manager, 1000));

  const std::vector<uint8_t> model_bytes{'C','H','M','-','R','N','N','-','v','1'};
  std::string digest;
  const bool hashed = sha256_hex(model_bytes, digest);
  ModelAdapterRegistry registry;
  check("compute SHA-256 over model bytes", hashed && digest.size() == 64);
  check("register valid manifest", hashed && registry.register_trusted_model("chimera-rnn-v1", digest));
  check("load digest-matching model", hashed && registry.load_and_verify_model("chimera-rnn-v1", model_bytes));
  auto tampered = model_bytes; tampered[0] ^= 1;
  check("reject tampered model bytes", !registry.load_and_verify_model("chimera-rnn-v1", tampered));
  check("unknown model unavailable", registry.get_model("unknown") == nullptr);
  std::cout << (failures ? "SECURITY ADAPTER TESTS FAILED: " : "SECURITY ADAPTER TESTS PASSED: ")
            << failures << " failure(s)\n";
  return failures ? 1 : 0;
}

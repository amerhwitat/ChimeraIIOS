#pragma once
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace chimera::quantum {

enum class Gate : std::uint8_t { X, Y, Z, H, S, T, CNOT, Measure };
struct Operation { Gate gate; std::uint32_t q0; std::uint32_t q1; };

// QuantumHybrid is intentionally an intermediate representation boundary.
// It can target a simulator or a real provider without changing kernel/ISA code.
class Circuit {
public:
    explicit Circuit(std::uint32_t qubits = 0) : qubits_(qubits) {}
    void reserve(std::size_t n) { ops_.reserve(n); }
    void append(Operation op) { ops_.push_back(op); }
    std::uint32_t qubits() const noexcept { return qubits_; }
    std::span<const Operation> operations() const noexcept { return ops_; }
private:
    std::uint32_t qubits_;
    std::vector<Operation> ops_;
};

struct BackendInfo {
    std::string name;
    std::uint32_t max_qubits{0};
    bool hardware{false};
};

class Backend {
public:
    virtual ~Backend() = default;
    virtual BackendInfo info() const = 0;
    virtual bool execute(const Circuit&) = 0;
};

} // namespace chimera::quantum

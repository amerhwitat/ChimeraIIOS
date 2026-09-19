#pragma once
#include <array>
#include <string_view>

namespace chimera::ai {
enum class Discipline { ML, DeepLearning, ReinforcementLearning, SymbolicAI, ComputerVision, NLP };
enum class DataKind { Structured, Tensor, Interaction, Knowledge, ImageVideo3D, TextSpeech };
struct JobSpec {
    Discipline discipline;
    DataKind data_kind;
    std::string_view task;
    std::string_view framework{};
};
inline constexpr std::array<Discipline, 6> kAllDisciplines{{
    Discipline::ML, Discipline::DeepLearning, Discipline::ReinforcementLearning,
    Discipline::SymbolicAI, Discipline::ComputerVision, Discipline::NLP
}};
}

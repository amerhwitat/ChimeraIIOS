#include <algorithm>
#include <cmath>
#include <numeric>
#include <string>
#include <vector>

namespace chm::neural {

struct Evidence { double value; double weight; };
struct Response { double score; double confidence; };

inline double clamp01(double x) { return std::clamp(x, 0.0, 1.0); }

inline Response reason(const std::vector<Evidence>& evidence) {
    double weighted = 0.0, weights = 0.0;
    for (const auto& e : evidence) {
        const double w = std::max(0.0, e.weight);
        weighted += clamp01(e.value) * w;
        weights += w;
    }
    if (weights == 0.0) return {0.0, 0.0};
    const double score = clamp01(weighted / weights);
    // Confidence is deliberately conservative: agreement and total support both matter.
    double variance = 0.0;
    for (const auto& e : evidence) {
        const double w = std::max(0.0, e.weight);
        const double d = clamp01(e.value) - score;
        variance += w * d * d;
    }
    const double spread = std::sqrt(variance / weights);
    return {score, clamp01(score * (1.0 - spread))};
}

inline std::vector<double> weighted_perception(const std::vector<double>& x,
                                               const std::vector<double>& confidence) {
    std::vector<double> out(x.size(), 0.0);
    for (std::size_t i = 0; i < x.size(); ++i)
        out[i] = x[i] * (i < confidence.size() ? clamp01(confidence[i]) : 1.0);
    return out;
}

} // namespace chm::neural

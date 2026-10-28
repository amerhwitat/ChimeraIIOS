// Research-only multidimensional tensor and neural-perception demonstrator.
// This is NOT kernel code, a quantum-gravity model, or a consciousness detector.
// Build: c++ -std=c++17 -O2 -Wall -Wextra -pedantic multidim_neural_perception.cpp -o multidim-neural
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace ChimeraOS::Multidim {
enum Dimension14 : std::size_t {
    X, Y, Z, TIME, PERSPECTIVE, ENERGY, INTERACTION, OBJECT_ID, MATERIAL,
    INFORMATION, UNCERTAINTY, AGENCY, SEMANTIC, CONSCIOUS
};
struct Matter14D {
    std::array<double, 14> d{};
    Matter14D() = default;
    Matter14D(std::initializer_list<double> values) {
        if (values.size() > d.size()) throw std::invalid_argument("Matter14D takes at most 14 values");
        std::copy(values.begin(), values.end(), d.begin());
    }
};

inline std::size_t element_count(const std::vector<std::size_t>& shape) {
    std::size_t n = 1;
    for (auto dim : shape) {
        if (dim == 0) throw std::invalid_argument("zero-sized tensor dimensions are unsupported");
        if (n > static_cast<std::size_t>(-1) / dim) throw std::overflow_error("tensor shape overflow");
        n *= dim;
    }
    return n;
}
inline std::size_t flatten_index(const std::vector<std::size_t>& index,
                                 const std::vector<std::size_t>& shape) {
    if (index.size() != shape.size()) throw std::invalid_argument("index rank mismatch");
    std::size_t flat = 0;
    for (std::size_t i = 0; i < shape.size(); ++i) {
        if (index[i] >= shape[i]) throw std::out_of_range("tensor index out of range");
        flat = flat * shape[i] + index[i];
    }
    return flat;
}

struct Tensor;
using TensorPtr = std::shared_ptr<Tensor>;
struct Tensor {
    std::vector<double> data, grad;
    std::vector<std::size_t> shape;
    std::vector<TensorPtr> parents;
    std::function<void(const Tensor&)> backward_fn;
    Tensor(std::vector<double> values, std::vector<std::size_t> dimensions)
        : data(std::move(values)), shape(std::move(dimensions)) {
        if (element_count(shape) != data.size()) throw std::invalid_argument("tensor data/shape mismatch");
        grad.assign(data.size(), 0.0);
    }
    std::size_t size() const { return data.size(); }
    void zero_grad() { std::fill(grad.begin(), grad.end(), 0.0); }
    void backward() {
        if (data.empty()) throw std::logic_error("cannot backpropagate an empty tensor");
        std::vector<TensorPtr> topo;
        std::set<const Tensor*> visited;
        std::function<void(const TensorPtr&)> visit = [&](const TensorPtr& node) {
            if (!node || !visited.insert(node.get()).second) return;
            for (const auto& p : node->parents) visit(p);
            topo.push_back(node);
        };
        // Caller owns the root via shared_ptr; recover a non-owning handle for traversal.
        TensorPtr root(this, [](Tensor*) {});
        visit(root);
        std::fill(grad.begin(), grad.end(), 1.0);
        for (auto it = topo.rbegin(); it != topo.rend(); ++it)
            if ((*it)->backward_fn) (*it)->backward_fn(**it);
    }
};
inline TensorPtr tensor_add(const TensorPtr& a, const TensorPtr& b) {
    if (!a || !b || a->shape != b->shape) throw std::invalid_argument("tensor_add shape mismatch");
    std::vector<double> out(a->size());
    for (std::size_t i = 0; i < out.size(); ++i) out[i] = a->data[i] + b->data[i];
    auto r = std::make_shared<Tensor>(std::move(out), a->shape);
    r->parents = {a, b};
    r->backward_fn = [a, b](const Tensor& self) {
        for (std::size_t i = 0; i < self.grad.size(); ++i) {
            a->grad[i] += self.grad[i]; b->grad[i] += self.grad[i];
        }
    };
    return r;
}
inline TensorPtr tensor_sigmoid(const TensorPtr& x) {
    if (!x) throw std::invalid_argument("null tensor");
    std::vector<double> out(x->size());
    for (std::size_t i = 0; i < out.size(); ++i)
        out[i] = 1.0 / (1.0 + std::exp(-x->data[i]));
    auto r = std::make_shared<Tensor>(std::move(out), x->shape);
    r->parents = {x};
    r->backward_fn = [x](const Tensor& self) {
        for (std::size_t i = 0; i < self.grad.size(); ++i)
            x->grad[i] += self.grad[i] * self.data[i] * (1.0 - self.data[i]);
    };
    return r;
}

struct EinsumSpec { std::vector<std::string> inputs; std::string output; };
inline EinsumSpec parse_einsum(const std::string& eq) {
    const auto arrow = eq.find("->");
    if (arrow == std::string::npos || eq.find("->", arrow + 2) != std::string::npos)
        throw std::invalid_argument("einsum requires one explicit -> output");
    EinsumSpec s; s.output = eq.substr(arrow + 2);
    std::size_t start = 0;
    const auto lhs = eq.substr(0, arrow);
    while (true) {
        auto comma = lhs.find(',', start);
        s.inputs.push_back(lhs.substr(start, comma == std::string::npos ? comma : comma - start));
        if (comma == std::string::npos) break;
        start = comma + 1;
    }
    if (s.inputs.empty() || s.inputs.size() != 0 && s.inputs.front().empty())
        throw std::invalid_argument("einsum has empty input specification");
    return s;
}
inline TensorPtr einsum(const std::string& equation, const std::vector<TensorPtr>& tensors) {
    auto spec = parse_einsum(equation);
    if (tensors.size() != spec.inputs.size()) throw std::invalid_argument("einsum input count mismatch");
    std::map<char, std::size_t> dims;
    std::set<char> all;
    for (std::size_t t = 0; t < tensors.size(); ++t) {
        if (!tensors[t]) throw std::invalid_argument("einsum received null tensor");
        if (spec.inputs[t].size() != tensors[t]->shape.size())
            throw std::invalid_argument("einsum input rank mismatch");
        std::set<char> seen;
        for (std::size_t axis = 0; axis < spec.inputs[t].size(); ++axis) {
            char label = spec.inputs[t][axis];
            if (label == ' ' || label == '.' || !seen.insert(label).second)
                throw std::invalid_argument("einsum labels must be unique single characters per input");
            auto [it, inserted] = dims.emplace(label, tensors[t]->shape[axis]);
            if (!inserted && it->second != tensors[t]->shape[axis])
                throw std::invalid_argument("einsum dimension mismatch");
            all.insert(label);
        }
    }
    std::set<char> output_seen;
    std::vector<std::size_t> out_shape;
    for (char c : spec.output) {
        auto it = dims.find(c);
        if (it == dims.end() || !output_seen.insert(c).second)
            throw std::invalid_argument("einsum output label invalid or repeated");
        out_shape.push_back(it->second);
    }
    for (char c : spec.output) all.erase(c);
    std::vector<char> labels(all.begin(), all.end());
    auto result = std::make_shared<Tensor>(
        std::vector<double>(element_count(out_shape), 0.0), out_shape);
    std::map<char, std::size_t> index;
    std::function<void(std::size_t)> loop = [&](std::size_t k) {
        if (k < labels.size()) {
            const char c = labels[k];
            for (std::size_t i = 0; i < dims.at(c); ++i) { index[c] = i; loop(k + 1); }
            return;
        }
        double product = 1.0;
        for (std::size_t t = 0; t < tensors.size(); ++t) {
            std::vector<std::size_t> ix;
            for (char c : spec.inputs[t]) ix.push_back(index.at(c));
            product *= tensors[t]->data[flatten_index(ix, tensors[t]->shape)];
        }
        std::vector<std::size_t> oi;
        for (char c : spec.output) oi.push_back(index.at(c));
        result->data[flatten_index(oi, result->shape)] += product;
    };
    loop(0);
    return result;
}

struct SensoryInputCV {
    double r{}, g{}, b{}, intensity{}, depth{}, motion{};
    std::vector<double> toVector() const { return {r, g, b, intensity, depth, motion}; }
};
class NeuralPerceptionLayer {
    std::vector<std::vector<double>> weights;
    std::vector<double> bias;
public:
    NeuralPerceptionLayer(std::size_t inputs, std::size_t outputs, std::uint32_t seed = 42) {
        if (!inputs || !outputs) throw std::invalid_argument("layer dimensions must be positive");
        std::mt19937 gen(seed);
        std::uniform_real_distribution<double> dist(-0.5, 0.5);
        weights.assign(outputs, std::vector<double>(inputs));
        bias.resize(outputs);
        for (std::size_t i = 0; i < outputs; ++i) {
            bias[i] = dist(gen);
            for (double& w : weights[i]) w = dist(gen);
        }
    }
    std::vector<double> forward(const std::vector<double>& input) const {
        if (input.size() != (weights.empty() ? 0 : weights.front().size()))
            throw std::invalid_argument("perception input size mismatch");
        std::vector<double> out(weights.size());
        for (std::size_t i = 0; i < weights.size(); ++i) {
            double sum = bias[i];
            for (std::size_t j = 0; j < input.size(); ++j) sum += weights[i][j] * input[j];
            out[i] = 1.0 / (1.0 + std::exp(-sum));
        }
        return out;
    }
};
struct SpinNodeCV {
    Matter14D state;
    NeuralPerceptionLayer brain{14, 14};
    std::vector<std::size_t> neighbors;
    std::vector<double> spins;
};
class SpinNetworkUniverse {
public:
    std::vector<SpinNodeCV> nodes;
    std::size_t addNode(const Matter14D& m) { SpinNodeCV n; n.state = m; nodes.push_back(std::move(n)); return nodes.size()-1; }
    void addEdge(std::size_t a, std::size_t b, double weight) {
        if (a >= nodes.size() || b >= nodes.size() || a == b || !std::isfinite(weight))
            throw std::invalid_argument("invalid spin-network edge");
        nodes[a].neighbors.push_back(b); nodes[a].spins.push_back(weight);
        nodes[b].neighbors.push_back(a); nodes[b].spins.push_back(weight);
    }
    void propagateUniverse(double alpha = 0.05) {
        if (!std::isfinite(alpha) || alpha < 0.0 || alpha > 1.0)
            throw std::invalid_argument("alpha must be in [0,1]");
        std::vector<Matter14D> next(nodes.size());
        for (std::size_t i = 0; i < nodes.size(); ++i) {
            std::vector<double> in(nodes[i].state.d.begin(), nodes[i].state.d.end());
            auto perceived = nodes[i].brain.forward(in);
            for (std::size_t d = 0; d < 14; ++d) next[i].d[d] = (1.0-alpha)*perceived[d];
            for (std::size_t e = 0; e < nodes[i].neighbors.size(); ++e) {
                const auto j = nodes[i].neighbors[e];
                for (std::size_t d = 0; d < 14; ++d) next[i].d[d] += alpha*nodes[i].spins[e]*nodes[j].state.d[d];
            }
            next[i].d[TIME] += 1.0;
        }
        for (std::size_t i = 0; i < nodes.size(); ++i) nodes[i].state = next[i];
    }
};
} // namespace ChimeraOS::Multidim

int main() {
    using namespace ChimeraOS::Multidim;
    Matter14D matter{1,1,1,0,1,1,1,1,1,0.8,0.2,0.9,0.9,0.85};
    SpinNetworkUniverse universe;
    auto a = universe.addNode(matter), b = universe.addNode(matter), c = universe.addNode(matter);
    universe.addEdge(a,b,0.85); universe.addEdge(b,c,0.70); universe.addEdge(a,c,0.50);
    for (int step=1; step<=5; ++step) {
        universe.propagateUniverse();
        std::cout << "step=" << step << " perception-index=" << universe.nodes[a].state.d[CONSCIOUS]
                  << " time=" << universe.nodes[a].state.d[TIME] << '\n';
    }
    auto x = std::make_shared<Tensor>(std::vector<double>{0.5,0.7,0.9,1.0}, std::vector<std::size_t>{2,2});
    auto y = std::make_shared<Tensor>(std::vector<double>{0.2,0.8,0.6,0.4}, std::vector<std::size_t>{2,2});
    auto z = einsum("td,dp->tp", {x,y});
    if (z->size() != 4 || std::abs(z->data[0] - 0.52) > 1e-9) return 2;
    auto s = tensor_sigmoid(tensor_add(x,y));
    s->backward();
    if (x->grad.size() != 4 || !std::isfinite(x->grad[0])) return 3;
    SensoryInputCV horizon{0.4,0.6,1.0,0.9,1000.0,0.0};
    NeuralPerceptionLayer cv(6,4);
    const auto perception = cv.forward(horizon.toVector());
    if (perception.size() != 4) return 4;
    std::cout << "einsum-elements=" << z->size() << " cv-outputs=" << perception.size() << '\n';
    return 0;
}

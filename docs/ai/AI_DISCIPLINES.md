# Chimera II OS AI Disciplines

## Six core disciplines

| Discipline | Core computational contract | Data | Runtime targets |
|---|---|---|---|
| ML | feature → estimator → metric | structured/tabular | native/Python/container |
| DL | tensor graph → training/inference | text/audio/image/tensor | CPU/GPU/container |
| RL | observation → action → reward → transition | interaction/simulation | native/CVEL/container |
| Symbolic AI | facts + rules + query → proof/result | rules/ontology/knowledge graph | native/Python/container |
| CV | pixels/geometry → spatial representation | image/video/3D | CPU/GPU/CVEL |
| NLP | text/speech → linguistic/neural representation | corpora/text/audio | CPU/GPU/container |

## External ecosystems used as references

The design follows public interfaces and documented concepts from scikit-learn, PyTorch, Gymnasium, Stable-Baselines3, SymPy, OpenCV/scikit-image, spaCy, Hugging Face Transformers, MLflow, Kubeflow, ONNX and Apache TVM.

scikit-learn explicitly separates its classical ML scope from deep learning and reinforcement learning, so Chimera keeps those disciplines as independent contracts. Gymnasium provides the standard `reset`/`step` environment model used by the RL adapter. spaCy models NLP as composable pipeline components, while its transformer component can consume Hugging Face transformer models. SymPy provides symbolic computation and code-generation APIs. Apache TVM provides a model import/optimization/deployment layer that can target non-Python runtimes.

## Cross-discipline modes

The Fabric supports combinations such as:

- **Neuro-symbolic:** DL/NLP/CV output feeding symbolic rules.
- **Vision-language:** CV embeddings combined with NLP/transformer models.
- **RL + CV:** visual observations feeding an agent policy.
- **NLP + symbolic:** retrieval/rules validating generated language.
- **ML + MLOps:** experiment manifests, metrics and model versions.
- **All + CVEL:** reproducible VM-based model validation before deployment.

Model/data provenance, seeds, metrics, provider versions and hardware requirements belong to every training or inference manifest.

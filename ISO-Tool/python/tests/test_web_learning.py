from iso_tool.neural_engine import NeuralEngine
from iso_tool.learning_engine import ingest_repository
def test_rnn(): assert NeuralEngine().train_from_build_sequences([[1,2,3]])['samples']==1
def test_ingest(tmp_path): (tmp_path/'README.md').write_text('cmake'); assert ingest_repository(tmp_path,tmp_path/'k.jsonl')['records']==1

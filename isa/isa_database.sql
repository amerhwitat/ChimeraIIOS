-- Chimera II OS ISA SQLite schema. Load rows from isa_database.json with tools/load_isa_database.py.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS architectures(
  id TEXT PRIMARY KEY,
  class TEXT NOT NULL,
  family TEXT NOT NULL,
  word_bits INTEGER NOT NULL,
  status TEXT NOT NULL,
  encoding_model TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  instruction_forms INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sources(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS instructions(
  architecture TEXT NOT NULL REFERENCES architectures(id),
  mnemonic TEXT NOT NULL,
  form_id TEXT NOT NULL,
  operands_json TEXT NOT NULL,
  syntax TEXT NOT NULL,
  length_bits INTEGER NOT NULL,
  value_bits TEXT NOT NULL,
  mask_bits TEXT NOT NULL,
  PRIMARY KEY(architecture,mnemonic,form_id)
);
CREATE INDEX IF NOT EXISTS idx_instruction_mnemonic ON instructions(mnemonic);
CREATE INDEX IF NOT EXISTS idx_instruction_architecture ON instructions(architecture);
CREATE INDEX IF NOT EXISTS idx_instruction_length ON instructions(length_bits);
CREATE VIEW IF NOT EXISTS instruction_encoding AS
SELECT architecture,mnemonic,form_id,syntax,length_bits,value_bits,mask_bits FROM instructions;

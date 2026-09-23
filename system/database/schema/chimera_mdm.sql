-- Chimera Data Architecture reference schema.
CREATE SCHEMA IF NOT EXISTS chimera_mdm;
CREATE TABLE IF NOT EXISTS chimera_mdm.party(
 party_id BIGINT PRIMARY KEY, party_type VARCHAR(32) NOT NULL,
 canonical_name VARCHAR(512), status VARCHAR(32), created_at TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS chimera_mdm.party_xref(
 source_system VARCHAR(128) NOT NULL, source_key VARCHAR(512) NOT NULL,
 party_id BIGINT NOT NULL REFERENCES chimera_mdm.party(party_id),
 confidence DECIMAL(9,6), is_golden BOOLEAN NOT NULL DEFAULT FALSE,
 PRIMARY KEY(source_system,source_key)
);
CREATE TABLE IF NOT EXISTS chimera_mdm.party_hierarchy(
 parent_party_id BIGINT NOT NULL REFERENCES chimera_mdm.party(party_id),
 child_party_id BIGINT NOT NULL REFERENCES chimera_mdm.party(party_id),
 relation_type VARCHAR(64) NOT NULL,
 PRIMARY KEY(parent_party_id,child_party_id,relation_type)
);
CREATE TABLE IF NOT EXISTS chimera_mdm.audit_history(
 audit_id BIGINT PRIMARY KEY, entity_type VARCHAR(128) NOT NULL,
 entity_id BIGINT NOT NULL, operation VARCHAR(32) NOT NULL,
 source_system VARCHAR(128), changed_at TIMESTAMP NOT NULL, payload_json TEXT
);
CREATE INDEX IF NOT EXISTS party_xref_party_idx ON chimera_mdm.party_xref(party_id);
CREATE INDEX IF NOT EXISTS audit_entity_idx ON chimera_mdm.audit_history(entity_type,entity_id,changed_at);

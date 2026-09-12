import { createHash } from 'node:crypto';

export function encodeEnvelope({ nodeId, type, sequence, payload, capabilities = [], version = 1 }) {
  const canonical = JSON.stringify(payload, Object.keys(payload).sort());
  const payloadHash = createHash('sha256').update(canonical).digest('hex');
  return JSON.stringify({ version, type, node_id: nodeId, sequence, capabilities, payload_hash: payloadHash, payload }) + '\n';
}

export function decodeEnvelope(line) {
  const message = JSON.parse(line);
  const canonical = JSON.stringify(message.payload, Object.keys(message.payload).sort());
  const actual = createHash('sha256').update(canonical).digest('hex');
  if (actual !== message.payload_hash) throw new Error('payload integrity check failed');
  return message;
}

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const desktop = JSON.parse(fs.readFileSync(new URL('../desktop_profiles.json', import.meta.url), 'utf8'));
const retro = JSON.parse(fs.readFileSync(new URL('../retro_emulators.json', import.meta.url), 'utf8'));

test('desktop profile catalog has Aurora and Linux/Windows profile families', () => {
  assert.ok(desktop.profiles.some(p => p.id === 'aurora-native'));
  assert.ok(desktop.profiles.some(p => p.id === 'linux-gnome'));
  assert.ok(desktop.profiles.some(p => p.id === 'linux-kde-plasma'));
  assert.ok(desktop.profiles.some(p => p.id === 'windows-11'));
});

test('desktop profiles have stable IDs and modes', () => {
  for (const p of desktop.profiles) {
    assert.match(p.id, /^[a-z0-9-]+$/);
    assert.ok(p.mode);
  }
});

test('retro emulator catalog contains broad historical computer families', () => {
  const systems = new Set(retro.emulators.flatMap(e => e.systems));
  for (const expected of ['C64', 'Amiga', 'Apple II', 'ZX Spectrum', 'MSX', 'DOS', 'Atari ST', 'BBC Micro']) {
    assert.ok(systems.has(expected), `missing ${expected}`);
  }
});

test('emulator entries declare an execution boundary', () => {
  for (const e of retro.emulators) {
    assert.ok(e.id && e.title && e.backend && Array.isArray(e.systems));
    assert.ok(['browser-wasm', 'native', 'external'].includes(e.backend));
  }
});

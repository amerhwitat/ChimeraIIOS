import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const html = fs.readFileSync('web/aurora_terminal.html', 'utf8');
const js = fs.readFileSync('web/aurora_terminal.js', 'utf8');

test('Aurora terminal exposes selectable shell profiles and keyboard prompt', () => {
  for (const shell of ['bash', 'zsh', 'fish', 'cmd', 'powershell', 'chimera']) {
    assert.match(html, new RegExp('value="' + shell + '"'));
  }
  assert.match(html, /id="prompt"/);
  assert.match(html, /id="cmd"/);
});

test('Web terminal uses safe text nodes and virtual filesystem operations', () => {
  assert.match(js, /textContent/);
  assert.match(js, /const dirs=new Set/);
  assert.match(js, /const files=new Map/);
  for (const command of ['pwd', 'cd', 'ls', 'cat', 'mkdir', 'touch', 'rm', 'man', 'apropos']) {
    assert.ok(js.includes("cmd==='" + command + "'"), 'missing command ' + command);
  }
  assert.doesNotMatch(js, /innerHTML|eval\s*\(/);
  assert.match(js, /host execution and host-drive access are not available/);
});

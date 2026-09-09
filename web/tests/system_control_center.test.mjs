import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const root = new URL('../', import.meta.url);
const read = name => fs.readFileSync(new URL(name, root), 'utf8');

test('CSCC contract defines management sections and stable actions', () => {
  const data = JSON.parse(read('system_control_center.json'));
  assert.equal(data.schema, 'chimera-system-control-center/v1');
  for (const section of ['capabilities', 'process_fields', 'service_fields', 'kpi_fields', 'settings', 'actions']) assert.ok(data[section]);
  for (const action of ['process.stop-request','process.terminate-request','service.start-request','service.stop-request','service.restart-request','service.enable-request','service.disable-request','session.shutdown-request','session.reboot-request']) assert.ok(data.actions.some(x => x.id === action));
  assert.ok(data.kpi_fields.includes('source'));
  assert.ok(data.kpi_fields.includes('confidence'));
});

test('CSCC UI exposes professional management sections', () => {
  const html = read('system_control_center.html');
  const js = read('system_control_center.js');
  const css = read('system_control_center.css');
  for (const id of ['overview','processes','services','performance','settings','sessions','startup','recovery']) assert.match(html, new RegExp(`id=["']${id}["']`));
  for (const action of ['process.stop-request','process.terminate-request','service.start-request','service.stop-request','service.restart-request','service.enable-request','service.disable-request']) assert.match(js, new RegExp(action.replace('.', '\\.' )));
  assert.match(css, /backdrop-filter/);
});

test('Aurora registry exposes the Control Center', () => {
  const apps = JSON.parse(read('aurora_apps.json'));
  const all = apps.categories.flatMap(c => c.apps);
  const app = all.find(x => x.id === 'system-control-center');
  assert.ok(app);
  assert.equal(app.url, 'system_control_center.html');
});

test('Aurora shell has a dedicated Control Center launcher', () => {
  assert.match(read('aurora_shell.js'), /system_control_center\.html/);
  assert.match(read('aurora_shell.js'), /data-control-center/);
});

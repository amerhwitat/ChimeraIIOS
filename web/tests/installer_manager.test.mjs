import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const catalog = JSON.parse(fs.readFileSync(new URL('../installer_catalog.json', import.meta.url), 'utf8'));
const registry = JSON.parse(fs.readFileSync(new URL('../aurora_apps.json', import.meta.url), 'utf8'));
const html = fs.readFileSync(new URL('../installer_manager.html', import.meta.url), 'utf8');
const shell = fs.readFileSync(new URL('../aurora_shell.js', import.meta.url), 'utf8');

test('catalog covers Linux, Windows and Chimera package families', () => {
  const formats = new Set(catalog.package_formats.map(x => x.id));
  for (const id of ['deb','rpm','pacman','zypper','apk','flatpak','appimage','winget','msix','msi-exe','chimera-pkg']) assert.ok(formats.has(id));
});

test('catalog prevents browser host execution', () => {
  assert.equal(catalog.policy.native_install_requires_authorized_backend, true);
  assert.equal(catalog.policy.browser_never_executes_host_installers, true);
});

test('applications expose platform and format metadata', () => {
  for (const app of catalog.applications) {
    assert.ok(app.id && app.title && app.platforms.length > 0 && app.formats.length > 0);
    assert.ok(['native','web-catalog','dry-run'].includes(app.default_mode));
  }
});

test('Aurora registry exposes Installer Manager', () => {
  const apps = registry.categories.flatMap(c => c.apps);
  assert.ok(apps.some(a => a.id === 'installer-manager' && a.url === 'installer_manager.html'));
});

test('Installer Manager UI exposes core controls', () => {
  for (const id of ['search','platform','available','installed','details','install','dry-run','remove','update','backend-state']) assert.match(html, new RegExp(`id=["']${id}["']`));
  assert.match(html, /authorized backend/i);
});

test('Aurora launcher dynamically includes registered applications', () => {
  assert.match(shell, /aurora_apps\.json/);
  assert.match(shell, /data-menu/);
});

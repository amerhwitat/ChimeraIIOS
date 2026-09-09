import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const root=new URL('../',import.meta.url);
const read=p=>fs.readFileSync(new URL(p,root),'utf8');
test('Aurora glass desktop contract defines shared surface',()=>{const x=JSON.parse(read('aurora_glass_desktop.json'));assert.equal(x.desktop,'Aurora Wayland Glass');assert.equal(x.surface.mode,'desktop-canvas');assert.equal(x.surface.apps,'embedded-windows');assert.equal(x.web_parity.same_background,true);assert.equal(x.web_parity.same_surface_model,true)});
test('Aurora terminal profile references command and man databases',()=>{const x=JSON.parse(read('aurora_terminal_profile.json'));assert.equal(x.theme,'aurora-glass');assert.equal(x.database,'man_pages.json');assert.equal(x.command_catalog,'command_catalog.json');assert.equal(x.prompt,'aurora@chimera:~$')});
test('man database includes cross-platform and Chimera commands',()=>{const x=JSON.parse(read('man_pages.json'));for(const k of ['ls','ip','systemctl','man','gcc','g++','gdb','cdb','chimera','chimera-as','chimera-objdump','aurora'])assert.ok(x.entries[k],k)});
test('Aurora registry uses embedded desktop applications',()=>{const x=JSON.parse(read('aurora_apps.json'));assert.equal(x.launcher,'embedded-surface');const apps=x.categories.flatMap(c=>c.apps);assert.ok(apps.some(a=>a.id==='chimera-code'&&a.mode==='embedded'));assert.ok(apps.some(a=>a.id==='terminal'&&a.url==='aurora_terminal.html'))});

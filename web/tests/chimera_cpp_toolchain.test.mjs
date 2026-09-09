import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const root=new URL('../',import.meta.url);
const read=p=>fs.readFileSync(new URL(p,root),'utf8');

test('Chimera C++ toolchain catalog exposes host and Chimera targets',()=>{
 const x=JSON.parse(read('chimera_cpp_toolchain.json'));
 assert.ok(x.host_compilers.includes('gcc')); assert.ok(x.host_compilers.includes('g++'));
 assert.ok(x.host_compilers.includes('msvc')); assert.ok(x.standards.includes('c++23'));
 assert.ok(x.standards.includes('c++26-preview'));
 assert.ok(x.chimera_targets.includes('chimera-cisc')); assert.ok(x.chimera_targets.includes('chimera-risc'));
});

test('Chimera Code IDE is present',()=>{
 const html=read('chimera_code_ide.html');
 assert.match(html,/Chimera Code IDE/); assert.match(html,/GCC/); assert.match(html,/G\+\+/);
 assert.match(html,/Chimera CISC/); assert.match(html,/Chimera RISC/);
});

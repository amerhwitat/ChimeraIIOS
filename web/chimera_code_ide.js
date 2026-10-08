(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const compiler=$('compiler'), standard=$('standard'), build=$('build'), output=$('output'), editor=$('editor');
  const language=$('language'), fileInput=$('fileInput'), fileStatus=$('fileStatus');
  let currentName='main.cpp', dirty=false;
  const extensions={'.c':'c','.h':'c','.cc':'cpp','.cpp':'cpp','.cxx':'cpp','.hpp':'cpp','.asm':'asm','.s':'gas','.S':'gas','.json':'ncb','.txt':'text'};
  const targetList=[['chimera-cisc','Chimera CISC','Prototype ISA profile'],['chimera-risc','Chimera RISC','Prototype ISA profile'],['chimera-native','Chimera Native','Koronos target contract'],['host-native','Host C/C++','GCC / Clang / MSVC'],['chimera-emulator','Chimera Emulator','Reference simulation']];
  const targets=$('targets');
  targetList.forEach(([id,title,note])=>{const b=document.createElement('button');b.className='target-card';b.dataset.target=id;const strong=document.createElement('strong'),small=document.createElement('small');strong.textContent=title;small.textContent=note;b.append(strong,small);b.addEventListener('click',()=>{targets.querySelectorAll('.target-card').forEach(x=>x.classList.remove('active'));b.classList.add('active');});targets.appendChild(b);});
  targets.firstElementChild?.click();
  const markDirty=()=>{dirty=true;fileStatus.textContent=currentName+' · modified (not saved)';};
  editor.addEventListener('input',markDirty);
  language.addEventListener('change',()=>{currentName=language.value==='asm'?'main.asm':language.value==='gas'?'main.S':language.value==='c'?'main.c':language.value==='ncb'?'manifest.json':language.value==='text'?'notes.txt':'main.cpp';markDirty();});
  $('openBtn').addEventListener('click',()=>fileInput.click());
  fileInput.addEventListener('change',async()=>{const f=fileInput.files?.[0];if(!f)return;currentName=f.name;editor.value=await f.text();const ext='.'+(f.name.split('.').pop()||'');if(extensions[ext])language.value=extensions[ext];dirty=false;fileStatus.textContent=currentName+' · loaded locally';});
  $('saveBtn').addEventListener('click',()=>{const blob=new Blob([editor.value],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=currentName;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);dirty=false;fileStatus.textContent=currentName+' · downloaded';});
  function request(action){
    const target=targets.querySelector('.target-card.active')?.dataset.target||'host-native';
    if(action==='run'&&language.value==='asm'){output.textContent='Run is disabled for raw assembly. Assemble/link through a configured toolchain and execute only in an explicitly configured emulator or native runtime.';return;}
    const payload={action,language:language.value,filename:currentName,compiler:compiler.value,standard:standard.value,build_system:build.value,source:editor.value,target};
    output.textContent='Submitting '+action+' request to configured toolchain service…';
    fetch('/api/chimera/toolchain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      .then(async r=>{const t=await r.text();if(!r.ok)throw new Error('HTTP '+r.status+': '+t);return t;})
      .then(t=>{output.textContent=t||'Toolchain service returned an empty response.';})
      .catch(e=>{output.textContent='No working toolchain service is connected ('+e.message+'). Your source remains available; use Save source or install a native toolchain below.';});
  }
  $('buildBtn').addEventListener('click',()=>request('build'));$('runBtn').addEventListener('click',()=>request('run'));$('debugBtn').addEventListener('click',()=>request('debug'));
  fetch('aurora-ide-catalog.json').then(r=>{if(!r.ok)throw Error('catalog HTTP '+r.status);return r.json();}).then(data=>{
    const root=$('ideCatalog');root.replaceChildren();
    for(const item of data.ides){const card=document.createElement('article');card.className='ide-card';const h=document.createElement('h3'),p=document.createElement('p'),license=document.createElement('small'),a=document.createElement('a');h.textContent=item.name;p.textContent=item.description;license.textContent='License: '+item.license;a.href=item.download;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Official download / install instructions';card.append(h,p,license,document.createElement('br'),a);root.appendChild(card);}
  }).catch(e=>{$('ideCatalog').textContent='IDE catalog unavailable: '+e.message;});
})();

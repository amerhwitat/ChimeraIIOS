(() => {
  const $ = id => document.getElementById(id);
  const compiler = $('compiler'), standard = $('standard'), build = $('build');
  const output = $('output'), editor = $('editor');
  const targets = $('targets');
  const targetList = [
    ['chimera-cisc','Chimera CISC','ISA backend'],
    ['chimera-risc','Chimera RISC','ISA backend'],
    ['chimera-native','Chimera Native','Koronos runtime'],
    ['chimera-emulator','Chimera Emulator','portable simulation']
  ];
  targetList.forEach(([id,title,note]) => {
    const b = document.createElement('button');
    b.className = 'target-card'; b.dataset.target = id;
    b.innerHTML = `<strong>${title}</strong><small>${note}</small>`;
    b.onclick = () => { document.querySelectorAll('.target-card').forEach(x=>x.classList.remove('active')); b.classList.add('active'); output.textContent = `Target selected: ${title}`; };
    targets.appendChild(b);
  });
  targets.firstElementChild?.click();
  function request(action) {
    const payload = { action, compiler: compiler.value, standard: standard.value, build_system: build.value,
      source: editor.value, target: document.querySelector('.target-card.active')?.dataset.target || 'chimera-emulator' };
    output.textContent = `Preparing ${action}...\n${JSON.stringify(payload, null, 2)}\n\nNative execution requires the authorized Chimera toolchain adapter.`;
    fetch('/api/chimera/toolchain', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      .then(r => r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then(t => { output.textContent = t || 'Toolchain adapter returned no output.'; })
      .catch(() => {});
  }
  $('buildBtn').onclick = () => request('build');
  $('runBtn').onclick = () => request('run');
  $('debugBtn').onclick = () => request('debug');
})();

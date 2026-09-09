(() => {
  'use strict';
  const canvas = document.getElementById('aurora3dCanvas');
  const profileKey = 'chimera.desktop.profile';
  const profilesUrl = 'desktop_profiles.json';
  const state = { profile: localStorage.getItem(profileKey) || 'aurora-native', profiles: [] };
  const $ = id => document.getElementById(id);

  // Three.js provides the GPU scene; the HTML layer remains the accessible desktop UI.
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x071426, 0.018);
  const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 500);
  camera.position.set(0, 5, 22);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);

  const world = new THREE.Group();
  scene.add(world);
  world.add(new THREE.HemisphereLight(0xb9ddff, 0x07101d, 2.1));
  const sun = new THREE.DirectionalLight(0x9acfff, 2.5);
  sun.position.set(8, 12, 6); world.add(sun);

  const lake = new THREE.Mesh(new THREE.PlaneGeometry(180, 90), new THREE.MeshStandardMaterial({ color: 0x0a2038, roughness: .2, metalness: .25, transparent: true, opacity: .82 }));
  lake.rotation.x = -Math.PI / 2; lake.position.y = -3; world.add(lake);
  const mountains = new THREE.Group();
  for (let i = 0; i < 16; i++) {
    const h = 3 + Math.random() * 8, w = 5 + Math.random() * 8;
    const m = new THREE.Mesh(new THREE.ConeGeometry(w, h, 5), new THREE.MeshStandardMaterial({ color: 0x183a58, roughness: 1 }));
    m.position.set((i - 8) * 7 + Math.random() * 3, h / 2 - 3, -8 - Math.random() * 10);
    m.rotation.y = Math.random() * Math.PI; mountains.add(m);
  }
  world.add(mountains);
  const aurora = new THREE.Group();
  for (let i = 0; i < 9; i++) {
    const geo = new THREE.TorusGeometry(5 + i * .65, .025 + i * .008, 8, 160, Math.PI * 1.35);
    const mat = new THREE.MeshBasicMaterial({ color: i % 2 ? 0x8d7cff : 0x67dfff, transparent: true, opacity: .16 });
    const ring = new THREE.Mesh(geo, mat); ring.position.y = 3 + i * .35; ring.rotation.x = Math.PI / 2.5; ring.rotation.z = i * .08; aurora.add(ring);
  }
  world.add(aurora);
  const stars = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: 0xdaf3ff, size: .07, transparent: true, opacity: .7 }));
  const positions = [];
  for (let i = 0; i < 1200; i++) positions.push((Math.random() - .5) * 180, Math.random() * 55 - 5, -Math.random() * 100);
  stars.geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3)); world.add(stars);

  function applyProfile(id) {
    state.profile = id;
    localStorage.setItem(profileKey, id);
    const p = state.profiles.find(x => x.id === id);
    const title = p ? p.title : id;
    $('profileName').textContent = title;
    $('railProfile').textContent = title;
    $('modeLabel').textContent = p ? `${p.family} · ${p.mode}` : 'WebGL desktop renderer';
    $('launcher').classList.add('hidden');
  }
  function showWindow(title, html) {
    $('windowTitle').textContent = title; $('windowContent').innerHTML = html; $('window').classList.remove('hidden');
  }
  function app(name) {
    if (name === 'launcher') { $('launcher').classList.toggle('hidden'); return; }
    if (name === 'files') showWindow('Files', '<h2>Home</h2><p>Desktop · Documents · Downloads · Music · Pictures · Videos</p><div class="profile-list"><div class="profile-card">▰ Desktop</div><div class="profile-card">▰ Documents</div><div class="profile-card">▰ Downloads</div><div class="profile-card">▰ Projects</div></div>');
    else if (name === 'terminal') showWindow('Aurora Terminal', '<pre>Chimera II Web Terminal\n\nLinux/POSIX + Bash/Zsh + Windows CMD + PowerShell\nSandboxed documentation and command catalog\n\nchimera@aurora:~$ man ls</pre>');
    else if (name === 'code') showWindow('Chimera Code IDE', '<h2>Chimera Code</h2><p>C/C++20 · GCC/g++ compatibility · Chimera CISC/RISC targets</p><pre>int main() {\n  return 0;\n}</pre>');
    else if (name === 'browser') showWindow('Browser', '<h2>Web Workspace</h2><p>Safe embedded browser surface for the Chimera II Web UI.</p>');
    else if (name === 'settings') showWindow('Settings', '<h2>Desktop Settings</h2><p>Glass effects · accessibility · renderer · profile selection</p>');
    else if (name === 'help') showWindow('Unified Help', '<h2>man / help</h2><p>Use <b>man PAGE</b>, <b>man SECTION PAGE</b>, or <b>man NAMESPACE:PAGE</b>. Linux, POSIX, BSD, Bash, Zsh, Windows and PowerShell sources are exposed through the unified help layer.</p>');
    else if (name === 'desktop') showDesktopProfiles();
    else if (name === 'search') $('desktopSearch').focus();
    else if (name === 'home') { $('launcher').classList.add('hidden'); $('window').classList.add('hidden'); }
  }
  function showDesktopProfiles() {
    const cards = state.profiles.map(p => `<button class="profile-card" data-profile="${p.id}"><b>${p.title}</b><br><small>${p.family} · ${p.mode}</small></button>`).join('');
    showWindow('Desktop Profiles', `<p>Visual Web adapters for Linux and Windows families. A real host session/VM/RDP is only used when an authorized backend is configured.</p><div class="profile-list">${cards}</div>`);
    document.querySelectorAll('[data-profile]').forEach(b => b.onclick = () => { applyProfile(b.dataset.profile); showDesktopProfiles(); });
  }
  document.querySelectorAll('[data-app]').forEach(b => b.addEventListener('click', () => app(b.dataset.app)));
  $('launcherButton').onclick = () => app('launcher'); $('dockLauncher').onclick = () => app('launcher');
  document.querySelectorAll('[data-window]').forEach(b => b.onclick = () => { if (b.dataset.window === 'close') $('window').classList.add('hidden'); if (b.dataset.window === 'min') $('window').classList.add('hidden'); if (b.dataset.window === 'max') $('window').style.inset = '8% 6% 12% 8%'; });
  $('desktopSearch').addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.value.trim()) showWindow('Desktop Search', `<h2>Search</h2><p>Searching unified desktop catalog for <b>${e.target.value.replace(/[<>&]/g,'')}</b>.</p>`); });
  fetch(profilesUrl, { cache: 'no-store' }).then(r => r.json()).then(c => { state.profiles = c.profiles || []; applyProfile(state.profile); }).catch(() => applyProfile(state.profile));
  function clock() { const d = new Date(); $('clock').textContent = d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); $('timeLarge').textContent = d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); $('dateText').textContent = d.toLocaleDateString([], {weekday:'long', month:'long', day:'numeric', year:'numeric'}); }
  setInterval(clock, 1000); clock();
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }
  addEventListener('resize', resize);
  addEventListener('pointermove', e => { world.rotation.y += ((e.clientX / innerWidth) - .5) * .0007; world.rotation.x = ((e.clientY / innerHeight) - .5) * -.025; });
  function animate(t) { requestAnimationFrame(animate); aurora.rotation.y = t * .00005; stars.rotation.y = t * .000003; renderer.render(scene, camera); }
  animate(0);
})();

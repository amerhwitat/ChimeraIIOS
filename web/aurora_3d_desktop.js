(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const profileKey = 'chimera.desktop.profile';
  const profilesUrl = 'desktop_profiles.json';
  const state = { profile: localStorage.getItem(profileKey) || 'aurora-native', profiles: [], maximized: false };
  let scene, camera, renderer, world, aurora, stars;

  // Input + system sound layer. Keep the UI interactive even if WebGL, CDN assets, or audio are unavailable.
  const input = { pointerId: null, dragging: false, dragX: 0, dragY: 0, windowX: 0, windowY: 0 };
  const audio = { ctx: null, master: 0.055, enabled: true };

  function ensureAudio() {
    if (!audio.enabled) return null;
    try {
      if (!audio.ctx) audio.ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (audio.ctx.state === 'suspended') audio.ctx.resume().catch(() => {});
      return audio.ctx;
    } catch (_) { return null; }
  }
  function systemSound(kind='click') {
    const ctx = ensureAudio();
    if (!ctx) return;
    const now = ctx.currentTime;
    const gain = ctx.createGain();
    const osc = ctx.createOscillator();
    const tones = {
      click:[520,0.045], open:[660,0.075], close:[240,0.09],
      error:[150,0.13], hover:[820,0.025], success:[880,0.11]
    };
    const [freq,dur] = tones[kind] || tones.click;
    osc.type = kind === 'error' ? 'sawtooth' : 'sine';
    osc.frequency.setValueAtTime(freq, now);
    osc.frequency.exponentialRampToValueAtTime(Math.max(70, freq * 0.72), now + dur);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(audio.master, now + 0.004);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start(now); osc.stop(now + dur + 0.01);
  }

  function showWindow(title, html) {
    $('windowTitle').textContent = title;
    $('windowContent').innerHTML = html;
    $('window').classList.remove('hidden');
    $('window').setAttribute('aria-hidden', 'false');
    systemSound('open');
  }
  function closeWindow() {
    $('window').classList.add('hidden');
    $('window').setAttribute('aria-hidden', 'true');
    systemSound('close');
  }
  function toggleLauncher(force) {
    const el = $('launcher');
    const open = force === undefined ? el.classList.contains('hidden') : !!force;
    el.classList.toggle('hidden', !open);
    el.setAttribute('aria-hidden', String(!open));
    if (open) systemSound('open');
  }
  function applyProfile(id) {
    state.profile = id;
    localStorage.setItem(profileKey, id);
    const p = state.profiles.find(x => x.id === id);
    const title = p ? p.title : id;
    $('profileName').textContent = title;
    $('railProfile').textContent = title;
    $('modeLabel').textContent = p ? `${p.family} · ${p.mode}` : 'WebGL desktop renderer';
    toggleLauncher(false);
  }
  function showDesktopProfiles() {
    const cards = state.profiles.length ? state.profiles.map(p =>
      `<button type="button" class="profile-card" data-profile="${p.id}"><b>${p.title}</b><br><small>${p.family} · ${p.mode}</small></button>`
    ).join('') : '<p>No profile catalog loaded; Aurora Native remains active.</p>';
    showWindow('Desktop Profiles', `<p>Visual Web adapters for Linux and Windows families. A real host session/VM/RDP is only used when an authorized backend is configured.</p><div class="profile-list">${cards}</div>`);
  }
  function app(name) {
    systemSound('click');
    if (name === 'launcher') { toggleLauncher(); return; }
    if (name === 'files') showWindow('Files', '<h2>Home</h2><p>Desktop · Documents · Downloads · Music · Pictures · Videos</p><div class="profile-list"><button type="button" class="profile-card">▰ Desktop</button><button type="button" class="profile-card">▰ Documents</button><button type="button" class="profile-card">▰ Downloads</button><button type="button" class="profile-card">▰ Projects</button></div>');
    else if (name === 'terminal') showWindow('Aurora Terminal', '<pre>Chimera II Web Terminal\\n\\nLinux/POSIX + Bash/Zsh + Windows CMD + PowerShell\\nSandboxed documentation and command catalog\\n\\nchimera@aurora:~$ man ls</pre>');
    else if (name === 'code') showWindow('Chimera Code IDE', '<h2>Chimera Code</h2><p>C/C++20 · GCC/g++ compatibility · Chimera CISC/RISC targets</p><pre>int main() {\\n  return 0;\\n}</pre>');
    else if (name === 'browser') showWindow('Browser', '<h2>Web Workspace</h2><p>Safe embedded browser surface for the Chimera II Web UI.</p>');
    else if (name === 'settings') showWindow('Settings', '<h2>Desktop Settings</h2><p>Glass effects · accessibility · renderer · profile selection</p><p><button type="button" class="profile-card" id="rendererToggle">Toggle 3D renderer</button></p>');
    else if (name === 'help') showWindow('Unified Help', '<h2>man / help</h2><p>Use <b>man PAGE</b>, <b>man SECTION PAGE</b>, or <b>man NAMESPACE:PAGE</b>.</p><h3>Input</h3><p>Mouse, pointer, touch, wheel, drag, right-click and keyboard shortcuts are supported.</p>');
    else if (name === 'desktop') showDesktopProfiles();
    else if (name === 'search') { $('desktopSearch').focus(); $('desktopSearch').select(); }
    else if (name === 'home') { toggleLauncher(false); closeWindow(); }
  }

  // Event delegation is intentional: it catches pinned apps, dock items and dynamic profile buttons.
  document.addEventListener('click', e => {
    const appButton = e.target.closest('[data-app]');
    if (appButton) { e.preventDefault(); app(appButton.dataset.app); return; }
    const profileButton = e.target.closest('[data-profile]');
    if (profileButton) { e.preventDefault(); applyProfile(profileButton.dataset.profile); showDesktopProfiles(); return; }
    const winButton = e.target.closest('[data-window]');
    if (winButton) {
      e.preventDefault();
      const action = winButton.dataset.window;
      if (action === 'close' || action === 'min') closeWindow();
      else if (action === 'max') {
        state.maximized = !state.maximized;
        $('window').classList.toggle('maximized', state.maximized);
        systemSound('click');
      }
      return;
    }
    if (e.target.closest('#launcherButton,#dockLauncher')) { e.preventDefault(); toggleLauncher(); }
  });
  document.addEventListener('pointerdown', e => {
    const hit = e.target.closest('button,input,.window-titlebar,.app-window,.launcher');
    if (hit) {
      ensureAudio();
      if (e.target.closest('button')) e.target.closest('button').classList.add('pressed');
      if (e.button === 0 && e.target.closest('.window-titlebar') && !e.target.closest('button')) {
        input.pointerId = e.pointerId; input.dragging = true;
        const w = $('window'), r = w.getBoundingClientRect();
        input.dragX = e.clientX; input.dragY = e.clientY; input.windowX = r.left; input.windowY = r.top;
        try { e.currentTarget.setPointerCapture(e.pointerId); } catch (_) {}
      }
    }
  }, {passive:true});
  document.addEventListener('pointerup', e => {
    const pressed = document.querySelectorAll('.pressed');
    pressed.forEach(x => x.classList.remove('pressed'));
    if (input.pointerId === e.pointerId) input.dragging = false;
  });
  document.addEventListener('pointercancel', () => { input.dragging = false; document.querySelectorAll('.pressed').forEach(x=>x.classList.remove('pressed')); });
  document.addEventListener('pointermove', e => {
    if (input.dragging && !state.maximized) {
      const w = $('window');
      const dx = e.clientX - input.dragX, dy = e.clientY - input.dragY;
      w.style.left = `${Math.max(0, input.windowX + dx)}px`;
      w.style.top = `${Math.max(0, input.windowY + dy)}px`;
    }
    if (world) {
      world.rotation.y = ((e.clientX / innerWidth) - .5) * .03;
      world.rotation.x = ((e.clientY / innerHeight) - .5) * -.025;
    }
  }, {passive:true});
  document.addEventListener('dblclick', e => {
    const title = e.target.closest('.window-titlebar');
    if (title && !e.target.closest('button')) {
      state.maximized = !state.maximized;
      $('window').classList.toggle('maximized', state.maximized);
      systemSound('click');
    }
  });
  document.addEventListener('contextmenu', e => {
    const interactive = e.target.closest('button,input,.app-window,.launcher');
    if (interactive) { e.stopPropagation(); systemSound('click'); }
  });
  document.addEventListener('wheel', e => {
    if (e.target.closest('.window-content,.launcher-main')) return;
    if (e.deltaY > 0 && !$('launcher').classList.contains('hidden')) toggleLauncher(false);
  }, {passive:true});
  document.addEventListener('keydown', e => {
    const mod = e.ctrlKey || e.metaKey;
    const key = e.key.toLowerCase();
    if (mod && key === 'k') { e.preventDefault(); app('search'); }
    else if (mod && e.code === 'Space') { e.preventDefault(); toggleLauncher(); }
    else if (e.key === 'Escape') {
      if (!$('launcher').classList.contains('hidden')) toggleLauncher(false);
      else if (!$('window').classList.contains('hidden')) closeWindow();
    } else if (e.altKey && e.key === 'F4') { e.preventDefault(); closeWindow(); }
    else if (mod && e.shiftKey && key === 'f') { e.preventDefault(); state.maximized=!state.maximized; $('window').classList.toggle('maximized',state.maximized); systemSound('click'); }
    else if (e.key === 'Enter' && document.activeElement?.matches('[data-app]')) { e.preventDefault(); document.activeElement.click(); }
    else if (e.key === ' ' && document.activeElement?.matches('button')) { e.preventDefault(); document.activeElement.click(); }
  });
  $('desktopSearch').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      const q = e.target.value.trim().replace(/[<>&]/g, '');
      showWindow('Desktop Search', `<h2>Search</h2><p>Searching unified desktop catalog for <b>${q}</b>.</p>`);
    }
    if (e.key === 'Escape') { e.target.value = ''; e.target.blur(); }
  });
  $('desktopSearch').addEventListener('focus', ensureAudio);

  function init3D() {
    if (!window.THREE) {
      $('modeLabel').textContent = 'WebGL renderer unavailable · UI fallback active';
      return;
    }
    try {
      const canvas = $('aurora3dCanvas');
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x071426, 0.018);
      camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 500);
      camera.position.set(0, 5, 22);
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
      renderer.setSize(innerWidth, innerHeight);
      world = new THREE.Group(); scene.add(world);
      world.add(new THREE.HemisphereLight(0xb9ddff, 0x07101d, 2.1));
      const sun = new THREE.DirectionalLight(0x9acfff, 2.5); sun.position.set(8, 12, 6); world.add(sun);
      const lake = new THREE.Mesh(new THREE.PlaneGeometry(180, 90), new THREE.MeshStandardMaterial({color:0x0a2038,roughness:.2,metalness:.25,transparent:true,opacity:.82}));
      lake.rotation.x=-Math.PI/2; lake.position.y=-3; world.add(lake);
      const mountains = new THREE.Group();
      for(let i=0;i<16;i++){const h=3+Math.random()*8,w=5+Math.random()*8,m=new THREE.Mesh(new THREE.ConeGeometry(w,h,5),new THREE.MeshStandardMaterial({color:0x183a58,roughness:1}));m.position.set((i-8)*7+Math.random()*3,h/2-3,-8-Math.random()*10);m.rotation.y=Math.random()*Math.PI;mountains.add(m);}
      world.add(mountains);
      aurora = new THREE.Group();
      for(let i=0;i<9;i++){const geo=new THREE.TorusGeometry(5+i*.65,.025+i*.008,8,160,Math.PI*1.35),mat=new THREE.MeshBasicMaterial({color:i%2?0x8d7cff:0x67dfff,transparent:true,opacity:.16}),ring=new THREE.Mesh(geo,mat);ring.position.y=3+i*.35;ring.rotation.x=Math.PI/2.5;ring.rotation.z=i*.08;aurora.add(ring);}
      world.add(aurora);
      stars = new THREE.Points(new THREE.BufferGeometry(),new THREE.PointsMaterial({color:0xdaf3ff,size:.07,transparent:true,opacity:.7}));
      const positions=[]; for(let i=0;i<1200;i++)positions.push((Math.random()-.5)*180,Math.random()*55-5,-Math.random()*100);
      stars.geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3)); world.add(stars);
      $('modeLabel').textContent = 'WebGL desktop renderer';
      function animate(t){requestAnimationFrame(animate);aurora.rotation.y=t*.00005;stars.rotation.y=t*.000003;renderer.render(scene,camera);}
      animate(0);
    } catch (err) {
      console.warn('Aurora 3D renderer disabled:', err);
      $('modeLabel').textContent = '3D renderer unavailable · UI fallback active';
    }
  }
  function clock(){const d=new Date();$('clock').textContent=d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});$('timeLarge').textContent=d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});$('dateText').textContent=d.toLocaleDateString([],{weekday:'long',month:'long',day:'numeric',year:'numeric'});}
  function resize(){if(!camera||!renderer)return;camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}
  addEventListener('resize',resize);
  addEventListener('pointermove',e=>{if(world){world.rotation.y=((e.clientX/innerWidth)-.5)*.03;world.rotation.x=((e.clientY/innerHeight)-.5)*-.025;}});
  fetch(profilesUrl,{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject()).then(c=>{state.profiles=c.profiles||[];applyProfile(state.profile);}).catch(()=>applyProfile(state.profile));
  setInterval(clock,1000); clock(); init3D();
})();
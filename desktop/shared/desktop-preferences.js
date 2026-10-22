/* Shared desktop preferences controller for Aurora and Marine prototypes.
 * Browser-persisted preferences affect this desktop UI only; hardware and OS-level
 * settings stay explicitly unavailable until a native capability adapter exists.
 */
(() => {
  'use strict';
  if (document.getElementById('os-preferences-launcher')) return;
  const isMarine = /\/marine\//i.test(location.pathname) || document.title.toLowerCase().includes('marine');
  const title = isMarine ? 'Settings' : 'System Preferences';
  const key = 'chimera.octavian.desktop.preferences.v1';
  const defaults = { accent: '#78e7e3', scale: 100, sounds: true, clickEffects: true, reduceMotion: false, developerMode: false, profile: 'balanced' };
  let prefs = { ...defaults };
  try { prefs = { ...defaults, ...JSON.parse(localStorage.getItem(key) || '{}') }; } catch (_) {}
  const save = () => { try { localStorage.setItem(key, JSON.stringify(prefs)); } catch (_) {} };
  const el = (tag, attrs = {}, text = '') => { const node = document.createElement(tag); Object.entries(attrs).forEach(([k,v]) => k === 'className' ? node.className = v : node.setAttribute(k, v)); if (text) node.textContent = text; return node; };
  const styleLink = el('link', { rel: 'stylesheet', href: new URL('desktop-preferences.css', document.currentScript.src).href });
  document.head.append(styleLink);
  const launcher = el('button', { id: 'os-preferences-launcher', type: 'button', 'aria-haspopup': 'dialog', title: title + ' (Ctrl+,)' }, '⚙ ' + title);
  document.body.append(launcher);
  const panel = el('section', { id: 'os-preferences-panel', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'os-preferences-title', hidden: '' });
  const header = el('header', { className: 'osp-header' });
  const heading = el('div');
  heading.append(el('div', { className: 'osp-eyebrow' }, isMarine ? 'OCTAVIANOS · MARINE' : 'CHIMERA / OCTAVIANOS · AURORA'));
  heading.append(el('h2', { id: 'os-preferences-title' }, title));
  heading.append(el('p', { className: 'osp-note' }, 'Shared desktop controls. Hardware-level settings require a native provider and are not simulated here.'));
  const close = el('button', { type: 'button', 'aria-label': 'Close preferences', className: 'osp-close' }, '×');
  header.append(heading, close); panel.append(header);
  const tabs = el('nav', { className: 'osp-tabs', 'aria-label': 'Preference categories' });
  const body = el('div', { className: 'osp-body' });
  const status = el('p', { className: 'osp-status', role: 'status', 'aria-live': 'polite' }, 'Preferences are stored in this browser for the current origin.');
  panel.append(tabs, body, status); document.body.append(panel);
  const sections = [
    { id: 'appearance', label: 'Appearance', description: 'Desktop accent, scaling, motion, and existing wallpaper picker.' },
    { id: 'interaction', label: 'Input & sound', description: 'Mouse click feedback and optional interface tones.' },
    { id: 'desktop', label: 'Desktop', description: 'Choose a UI profile and common keyboard shortcuts.' },
    { id: 'developer', label: 'Developer', description: 'Expose diagnostic overlays for desktop prototyping.' }
  ];
  let active = 'appearance';
  const field = (labelText, control, note) => { const wrap = el('label', { className: 'osp-field' }); const top = el('span', {}, labelText); wrap.append(top, control); if (note) wrap.append(el('small', {}, note)); return wrap; };
  const checkbox = (id, label, value, onChange) => { const input = el('input', { id, type: 'checkbox' }); input.checked = !!value; input.addEventListener('change', () => { onChange(input.checked); save(); apply(); }); return field(label, input); };
  const select = (id, label, options, value, onChange) => { const input = el('select', { id }); options.forEach(([v,t]) => { const opt = el('option', { value: v }, t); input.append(opt); }); input.value = String(value); input.addEventListener('change', () => { onChange(input.value); save(); apply(); }); return field(label, input); };
  const render = () => {
    tabs.replaceChildren(); body.replaceChildren();
    sections.forEach(s => { const b = el('button', { type: 'button', className: s.id === active ? 'active' : '' }, s.label); b.setAttribute('aria-pressed', String(s.id === active)); b.addEventListener('click', () => { active = s.id; render(); }); tabs.append(b); });
    const section = sections.find(s => s.id === active); body.append(el('p', { className: 'osp-description' }, section.description));
    if (active === 'appearance') {
      const accent = el('input', { type: 'color', value: prefs.accent, 'aria-label': 'Accent color' }); accent.value = prefs.accent; accent.addEventListener('input', () => { prefs.accent = accent.value; save(); apply(); });
      body.append(field('Accent color', accent, 'Applies to supported controls on this desktop page.'));
      body.append(select('osp-scale', 'Interface scale', [['90','90%'],['100','100%'],['110','110%'],['125','125%'],['150','150%']], prefs.scale, v => prefs.scale = Number(v)));
      body.append(checkbox('osp-motion', 'Reduce interface motion', prefs.reduceMotion, v => prefs.reduceMotion = v));
      const wallpaper = el('button', { type: 'button', className: 'osp-action' }, 'Open wallpaper picker'); wallpaper.addEventListener('click', () => { const b = document.getElementById('wallpaperButton'); if (b) b.click(); else status.textContent = 'This desktop does not expose its wallpaper picker.'; }); body.append(wallpaper);
    } else if (active === 'interaction') {
      body.append(checkbox('osp-sounds', 'Interface sounds', prefs.sounds, v => prefs.sounds = v));
      body.append(checkbox('osp-clicks', 'Mouse click visual feedback', prefs.clickEffects, v => prefs.clickEffects = v));
      body.append(el('p', { className: 'osp-note' }, 'Sound is generated locally after user interaction; no audio or input data is transmitted.'));
      const test = el('button', { type: 'button', className: 'osp-action' }, 'Test interface sound'); test.addEventListener('click', playTone); body.append(test);
    } else if (active === 'desktop') {
      body.append(select('osp-profile', 'Desktop interaction profile', [['balanced','Balanced'],['keyboard','Keyboard-first'],['pointer','Pointer-first'],['reduced-motion','Reduced motion']], prefs.profile, v => { prefs.profile = v; if (v === 'reduced-motion') prefs.reduceMotion = true; }));
      const list = el('ul', { className: 'osp-shortcuts' });
      [['Ctrl + ,','Open preferences'],['Ctrl + Alt + D','Toggle developer mode'],['Escape','Close preferences'],['Alt + 1…4','Switch workspace indicator']].forEach(([k,v]) => { const li = el('li'); li.append(el('kbd', {}, k), el('span', {}, v)); list.append(li); }); body.append(list);
      body.append(el('p', { className: 'osp-note' }, 'Workspace switching changes the prototype indicator only; native virtual desktop management is not claimed.'));
    } else {
      body.append(checkbox('osp-dev', 'Enable desktop developer overlay', prefs.developerMode, v => prefs.developerMode = v));
      body.append(el('p', { className: 'osp-note' }, 'Developer mode shows the current UI profile and preference state. It does not enable privileged kernel, driver, or firmware operations.'));
      const reset = el('button', { type: 'button', className: 'osp-action danger' }, 'Reset desktop preferences'); reset.addEventListener('click', () => { prefs = { ...defaults }; save(); apply(); render(); status.textContent = 'Browser desktop preferences reset.'; }); body.append(reset);
    }
  };
  const apply = () => {
    document.documentElement.style.setProperty('--accent', prefs.accent);
    document.documentElement.style.setProperty('--task', prefs.accent + '55');
    document.documentElement.style.fontSize = prefs.scale + '%';
    document.documentElement.dataset.reduceMotion = String(prefs.reduceMotion);
    document.documentElement.dataset.desktopProfile = prefs.profile;
    document.documentElement.dataset.developerMode = String(prefs.developerMode);
    let badge = document.getElementById('osp-dev-badge');
    if (prefs.developerMode && !badge) { badge = el('div', { id: 'osp-dev-badge' }); document.body.append(badge); }
    if (badge) { badge.hidden = !prefs.developerMode; badge.textContent = 'DEV · ' + prefs.profile + ' · browser-only settings'; }
  };
  const open = () => { panel.hidden = false; launcher.setAttribute('aria-expanded', 'true'); render(); close.focus(); };
  const shut = () => { panel.hidden = true; launcher.setAttribute('aria-expanded', 'false'); launcher.focus(); };
  launcher.addEventListener('click', open); close.addEventListener('click', shut);
  panel.addEventListener('click', e => { if (e.target === panel) shut(); });
  let audioContext;
  function playTone() { if (!prefs.sounds) { status.textContent = 'Interface sounds are disabled.'; return; } try { const Ctx = window.AudioContext || window.webkitAudioContext; if (!Ctx) throw new Error('Web Audio unavailable'); audioContext ||= new Ctx(); const osc = audioContext.createOscillator(), gain = audioContext.createGain(); osc.type = 'sine'; osc.frequency.value = 660; gain.gain.setValueAtTime(.045, audioContext.currentTime); gain.gain.exponentialRampToValueAtTime(.001, audioContext.currentTime + .09); osc.connect(gain); gain.connect(audioContext.destination); osc.start(); osc.stop(audioContext.currentTime + .1); } catch (_) { status.textContent = 'Audio playback is unavailable in this browser.'; } }
  document.addEventListener('click', e => { if (e.target.closest('#os-preferences-panel,#os-preferences-launcher')) return; if (prefs.clickEffects) { const ripple = el('span', { className: 'osp-ripple' }); ripple.style.left = e.clientX + 'px'; ripple.style.top = e.clientY + 'px'; document.body.append(ripple); setTimeout(() => ripple.remove(), 500); } if (prefs.sounds && e.target.closest('button,.shortcut,.deskicon,.taskapp,.tile,.app,.dock a')) playTone(); });
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === ',') { e.preventDefault(); panel.hidden ? open() : shut(); return; }
    if (e.key === 'Escape' && !panel.hidden) { shut(); return; }
    if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'd') { e.preventDefault(); prefs.developerMode = !prefs.developerMode; save(); apply(); status.textContent = 'Developer overlay ' + (prefs.developerMode ? 'enabled' : 'disabled') + '.'; }
    if (e.altKey && /^[1-4]$/.test(e.key)) { document.documentElement.dataset.workspace = e.key; const label = document.querySelector('.topitems span,.menus span'); if (label) label.setAttribute('title', 'Prototype workspace ' + e.key); status.textContent = 'Workspace indicator set to ' + e.key + ' (prototype only).'; }
  });
  apply();
})();
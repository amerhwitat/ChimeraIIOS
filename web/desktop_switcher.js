(() => {
  'use strict';

  const STORAGE_KEY = 'chimera.desktop.profile';
  const status = document.querySelector('#status');
  const profiles = document.querySelector('#profiles');
  let catalog = null;

  async function loadCatalog() {
    const response = await fetch('desktop_profiles.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    catalog = await response.json();
    render();
  }

  function render() {
    const current = localStorage.getItem(STORAGE_KEY) || catalog.default;
    profiles.innerHTML = catalog.profiles.map(profile => `
      <article class="card" style="padding:20px">
        <h2>${profile.title}</h2>
        <p>${profile.description}</p>
        <p><small>${profile.family} · ${profile.mode}</small></p>
        <button data-profile="${profile.id}">${profile.id === current ? 'Current desktop' : 'Switch to this desktop'}</button>
      </article>
    `).join('');
    const selected = catalog.profiles.find(profile => profile.id === current);
    status.textContent = `Current: ${selected ? selected.title : current}`;
  }

  profiles.addEventListener('click', event => {
    const button = event.target.closest('[data-profile]');
    if (!button || !catalog) return;
    localStorage.setItem(STORAGE_KEY, button.dataset.profile);
    window.dispatchEvent(new CustomEvent('chimera-desktop-change', {
      detail: { id: button.dataset.profile }
    }));
    render();
  });

  loadCatalog().catch(error => {
    status.textContent = `Desktop catalog unavailable: ${error.message}`;
  });
})();

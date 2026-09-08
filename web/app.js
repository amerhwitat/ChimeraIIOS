(() => {
  'use strict';

  const cards = [
    ['Native ISA', 'RegisterN / CPU8192', '1024 × 8192-bit GPR model with 128D research state'],
    ['RISC compatibility', 'RV32I / RV64I / AArch64', 'Normalized decode layer for open and published RISC families'],
    ['CISC compatibility', 'x86-64', 'Variable-length instruction frontend and common system/data classes'],
    ['Kernel', 'Scheduler · MM · VFS · IPC · Net', 'Linux-inspired subsystem boundaries without copying Linux source'],
    ['Graphics', 'Aurora Wayland', 'GPU, DMA-BUF, EGL and presentation architecture'],
    ['Research', '128D / C8192', 'Machine, cognitive and world-state experimentation']
  ];

  const isa = [
    ['Chimera-8192', 'Experimental wide-word', '8192', 'Native', 'Implemented core'],
    ['RV32I', 'RISC', '32', 'Compatibility', 'Decoder skeleton'],
    ['RV64I', 'RISC', '64', 'Compatibility', 'Decoder skeleton'],
    ['AArch64', 'RISC', '64', 'Compatibility', 'Decoder skeleton'],
    ['x86-64', 'CISC', '64', 'Compatibility', 'Decoder skeleton']
  ];

  const layers = [
    'Boot / firmware', 'ISA frontend', 'Koronos kernel core',
    'Scheduler + IRQ + syscall', 'Virtual memory / allocator', 'VFS + TensorFS',
    'IPC / zero-copy', 'Spotnik networking', 'CEF security/capabilities',
    'Aurora compositor / GPU'
  ];

  const $ = (selector) => document.querySelector(selector);
  const text = (value) => document.createTextNode(value);

  function createCard(item) {
    const article = document.createElement('article');
    article.className = 'card';
    const title = document.createElement('h3');
    title.appendChild(text(item[0]));
    const strong = document.createElement('strong');
    strong.appendChild(text(item[1]));
    const p = document.createElement('p');
    p.appendChild(text(item[2]));
    article.append(title, strong, p);
    return article;
  }

  function renderTable(rows, target) {
    const fragment = document.createDocumentFragment();
    rows.forEach((row) => {
      const tr = document.createElement('tr');
      row.forEach((cell) => {
        const td = document.createElement('td');
        td.appendChild(text(cell));
        tr.appendChild(td);
      });
      fragment.appendChild(tr);
    });
    target.replaceChildren(fragment);
  }

  function renderLayers(target) {
    const fragment = document.createDocumentFragment();
    layers.forEach((name, index) => {
      const item = document.createElement('div');
      item.className = 'layer';
      const number = document.createElement('span');
      number.className = 'layer-index';
      number.appendChild(text(`L${index}`));
      const label = document.createElement('strong');
      label.appendChild(text(name));
      item.append(number, label);
      fragment.appendChild(item);
    });
    target.replaceChildren(fragment);
  }

  function render() {
    const cardsTarget = $('#cards');
    const isaTarget = $('#isa');
    const kernelTarget = $('#kernel');
    if (!cardsTarget || !isaTarget || !kernelTarget) return;

    cardsTarget.replaceChildren(...cards.map(createCard));
    renderTable(isa, isaTarget);
    renderLayers(kernelTarget);

    const cardCount = $('#card-count');
    const layerCount = $('#layer-count');
    if (cardCount) cardCount.textContent = `${cards.length} domains`;
    if (layerCount) layerCount.textContent = `${layers.length} layers`;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', render, { once: true });
  } else {
    render();
  }
})();

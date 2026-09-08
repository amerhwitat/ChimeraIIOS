const MODES = ['Scalar', 'Vector', 'NativeWide', 'JIT', 'QuantumHybrid'];
const WIDTHS = [8,16,32,64,128,256,512,1024,2048,4096,8192,16384];

export function createNBitRuntime(root) {
  const state = { mode: 'NativeWide', bits: 8192 };
  root.innerHTML = `<section class="nbit-panel"><h2>N-bit Runtime</h2>
    <label>Execution mode <select id="nbit-mode">${MODES.map(m => `<option>${m}</option>`).join('')}</select></label>
    <label>Width <select id="nbit-width">${WIDTHS.map(w => `<option>${w}</option>`).join('')} </select> bits</label>
    <output id="nbit-status"></output></section>`;
  const mode = root.querySelector('#nbit-mode');
  const width = root.querySelector('#nbit-width');
  const status = root.querySelector('#nbit-status');
  mode.value = state.mode; width.value = String(state.bits);
  function render() {
    state.mode = mode.value; state.bits = Number(width.value);
    const quantum = state.mode === 'QuantumHybrid';
    status.textContent = `Chimera ${state.bits}-bit • ${state.mode}` + (quantum ? ' • QIR/backend boundary' : '');
    root.dispatchEvent(new CustomEvent('chimera-runtime-change', { detail: {...state} }));
  }
  mode.addEventListener('change', render); width.addEventListener('change', render); render();
  return { state };
}

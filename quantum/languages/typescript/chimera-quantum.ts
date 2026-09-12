export type Complex = { re: number; im: number };
export type Gate = 'X' | 'H' | 'Z';

export class StateVector {
  readonly amplitudes: Complex[];
  constructor(public readonly qubits: number) {
    if (qubits < 1) throw new Error('qubits must be positive');
    this.amplitudes = Array.from({length: 1 << qubits}, () => ({re: 0, im: 0}));
    this.amplitudes[0] = {re: 1, im: 0};
  }
  probabilitySum(): number { return this.amplitudes.reduce((s,a) => s + a.re*a.re + a.im*a.im, 0); }
  hadamard(target: number): void {
    if (target < 0 || target >= this.qubits) throw new RangeError('target');
    const bit = 1 << target, s = 1 / Math.sqrt(2);
    for (let i=0; i<this.amplitudes.length; i++) if ((i & bit) === 0) {
      const j = i | bit, x = this.amplitudes[i], y = this.amplitudes[j];
      this.amplitudes[i] = {re:s*(x.re+y.re), im:s*(x.im+y.im)};
      this.amplitudes[j] = {re:s*(x.re-y.re), im:s*(x.im-y.im)};
    }
  }
}

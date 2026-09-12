#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Complex { pub re: f64, pub im: f64 }

impl Complex {
    pub fn norm2(self) -> f64 { self.re * self.re + self.im * self.im }
    pub fn scale(self, s: f64) -> Self { Self { re: self.re * s, im: self.im * s } }
    pub fn add(self, b: Self) -> Self { Self { re: self.re + b.re, im: self.im + b.im } }
}

#[derive(Clone, Copy, Debug)]
pub enum Gate { X, Y, Z, H, Phase(f64) }

#[derive(Clone, Debug)]
pub struct StateVector { pub qubits: usize, pub amplitudes: Vec<Complex> }

impl StateVector {
    pub fn new(qubits: usize) -> Result<Self, &'static str> {
        if qubits >= usize::BITS as usize - 1 { return Err("qubit count is too large for host indexing"); }
        let n = 1usize << qubits;
        let mut amplitudes = vec![Complex::default(); n];
        amplitudes[0] = Complex { re: 1.0, im: 0.0 };
        Ok(Self { qubits, amplitudes })
    }

    pub fn apply_single(&mut self, gate: Gate, target: usize) -> Result<(), &'static str> {
        if target >= self.qubits { return Err("target qubit out of range"); }
        let bit = 1usize << target;
        let (a, b, c, d) = match gate {
            Gate::X => (Complex::default(), Complex { re: 1.0, im: 0.0 }, Complex { re: 1.0, im: 0.0 }, Complex::default()),
            Gate::Y => (Complex::default(), Complex { re: 0.0, im: -1.0 }, Complex { re: 0.0, im: 1.0 }, Complex::default()),
            Gate::Z => (Complex { re: 1.0, im: 0.0 }, Complex::default(), Complex::default(), Complex { re: -1.0, im: 0.0 }),
            Gate::H => { let s = 1.0 / 2.0_f64.sqrt(); (Complex { re: s, im: 0.0 }, Complex { re: s, im: 0.0 }, Complex { re: s, im: 0.0 }, Complex { re: -s, im: 0.0 }) },
            Gate::Phase(theta) => (Complex { re: 1.0, im: 0.0 }, Complex::default(), Complex::default(), Complex { re: theta.cos(), im: theta.sin() }),
        };
        for base in 0..self.amplitudes.len() {
            if base & bit != 0 { continue; }
            let j = base | bit;
            let x = self.amplitudes[base];
            let y = self.amplitudes[j];
            self.amplitudes[base] = a.scale(x.re).add(b.scale(y.re));
            self.amplitudes[j] = c.scale(x.re).add(d.scale(y.re));
            // Imaginary parts are handled explicitly below to keep Complex dependency-free.
            self.amplitudes[base].im = a.re * x.im + b.re * y.im + a.im * x.re + b.im * y.re;
            self.amplitudes[j].im = c.re * x.im + d.re * y.im + c.im * x.re + d.im * y.re;
        }
        Ok(())
    }

    pub fn probability_sum(&self) -> f64 { self.amplitudes.iter().map(|a| a.norm2()).sum() }

    pub fn probabilities(&self) -> Vec<f64> { self.amplitudes.iter().map(|a| a.norm2()).collect() }
}

pub fn bell_state() -> [Complex; 4] {
    let s = 1.0_f64 / 2.0_f64.sqrt();
    [Complex { re: s, im: 0.0 }, Complex::default(), Complex::default(), Complex { re: s, im: 0.0 }]
}

pub fn probability_sum(s: &[Complex]) -> f64 { s.iter().map(|x| x.norm2()).sum() }

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn bell_normalized() { assert!((probability_sum(&bell_state()) - 1.0).abs() < 1e-12); }
    #[test] fn hadamard_creates_equal_probabilities() {
        let mut s = StateVector::new(1).unwrap(); s.apply_single(Gate::H, 0).unwrap();
        let p = s.probabilities(); assert!((p[0] - 0.5).abs() < 1e-12); assert!((p[1] - 0.5).abs() < 1e-12);
    }
}

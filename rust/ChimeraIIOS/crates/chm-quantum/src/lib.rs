#[derive(Clone,Copy,Debug,Default)]pub struct Complex{pub re:f64,pub im:f64}
impl Complex{pub fn norm2(self)->f64{self.re*self.re+self.im*self.im}}
pub fn bell_state()->[Complex;4]{let s=1.0_f64/2.0_f64.sqrt();[Complex{re:s,im:0.0},Complex::default(),Complex::default(),Complex{re:s,im:0.0}]}
pub fn probability_sum(s:&[Complex])->f64{s.iter().map(|x|x.norm2()).sum()}
#[cfg(test)]mod tests{use super::*;#[test]fn bell_normalized(){assert!((probability_sum(&bell_state())-1.0).abs()<1e-12);}}

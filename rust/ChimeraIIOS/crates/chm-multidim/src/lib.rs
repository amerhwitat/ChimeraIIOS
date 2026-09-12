pub fn norm<const N:usize>(x:&[f64;N])->f64{x.iter().map(|v|v*v).sum::<f64>().sqrt()}
pub fn dot<const N:usize>(a:&[f64;N],b:&[f64;N])->f64{a.iter().zip(b).map(|(x,y)|x*y).sum()}
pub fn project<const N:usize>(x:&[f64;N],observer:&[f64;N])->[f64;N]{std::array::from_fn(|i|x[i]-observer[i])}
#[cfg(test)]mod tests{use super::*;#[test]fn norm_128(){let x=[1.0;128];assert!((norm(&x)-128.0_f64.sqrt()).abs()<1e-12);}}

pub fn norm<const N: usize>(x: &[f64; N]) -> f64 { x.iter().map(|v| v * v).sum::<f64>().sqrt() }

pub fn dot<const N: usize>(a: &[f64; N], b: &[f64; N]) -> f64 {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

pub fn project<const N: usize>(x: &[f64; N], observer: &[f64; N]) -> [f64; N] {
    std::array::from_fn(|i| x[i] - observer[i])
}

pub fn affine<const N: usize>(x: &[f64; N], scale: f64, translation: &[f64; N]) -> [f64; N] {
    std::array::from_fn(|i| scale * x[i] + translation[i])
}

pub fn normalize<const N: usize>(x: &[f64; N]) -> Option<[f64; N]> {
    let n = norm(x); if n == 0.0 { None } else { Some(std::array::from_fn(|i| x[i] / n)) }
}

#[derive(Clone, Copy, Debug)]
pub struct Observer<const N: usize> {
    pub origin: [f64; N],
    pub scale: f64,
}

impl<const N: usize> Observer<N> {
    pub fn observe(&self, point: &[f64; N]) -> [f64; N] {
        affine(&project(point, &self.origin), self.scale, &[0.0; N])
    }
}

#[derive(Clone, Copy, Debug)]
pub struct PerceptionOverlay<const N: usize> {
    pub confidence: [f64; N],
}

impl<const N: usize> PerceptionOverlay<N> {
    pub fn weighted<const M: usize>(&self, geometry: &[f64; N]) -> [f64; N] {
        let _ = M; std::array::from_fn(|i| geometry[i] * self.confidence[i])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn norm_128() { let x = [1.0; 128]; assert!((norm(&x) - 128.0_f64.sqrt()).abs() < 1e-12); }
    #[test] fn observer_translation() { let o = Observer { origin: [1.0, 2.0], scale: 1.0 }; assert_eq!(o.observe(&[3.0, 5.0]), [2.0, 3.0]); }
    #[test] fn normalized_unit_vector() { let x = [3.0, 4.0]; let n = normalize(&x).unwrap(); assert!((norm(&n) - 1.0).abs() < 1e-12); }
}

#[derive(Clone, Copy, Debug)]
pub struct Evidence { pub value: f64, pub weight: f64 }
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Response { pub score: f64, pub confidence: f64 }
fn c01(x: f64) -> f64 { x.clamp(0.0, 1.0) }
pub fn reason(items: &[Evidence]) -> Response {
    let total: f64 = items.iter().map(|e| e.weight.max(0.0)).sum();
    if total == 0.0 { return Response { score: 0.0, confidence: 0.0 }; }
    let score = items.iter().map(|e| c01(e.value) * e.weight.max(0.0)).sum::<f64>() / total;
    let var = items.iter().map(|e| e.weight.max(0.0) * (c01(e.value) - score).powi(2)).sum::<f64>() / total;
    Response { score: c01(score), confidence: c01(score * (1.0 - var.sqrt())) }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn confidence_is_bounded() {
        let r = reason(&[Evidence { value: 0.9, weight: 2.0 }, Evidence { value: 0.8, weight: 1.0 }]);
        assert!((0.0..=1.0).contains(&r.confidence));
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Backend { Null, WindowsSapi, LinuxSpeechDispatcher, PipeWire, CoreAudio, External }
#[derive(Clone, Debug)]
pub struct VoiceRequest { pub text: String, pub language: String, pub rate: f32, pub pitch: f32, pub volume: f32 }
pub fn validate(req: &VoiceRequest) -> Result<(), &'static str> {
    if req.text.is_empty() { return Err("empty text"); }
    if !(0.25..=4.0).contains(&req.rate) { return Err("rate outside supported range"); }
    if !(0.0..=1.0).contains(&req.volume) { return Err("volume outside supported range"); }
    Ok(())
}

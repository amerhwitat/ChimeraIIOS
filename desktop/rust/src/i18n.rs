#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction { Ltr, Rtl }
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Locale { pub id: &'static str, pub language: &'static str, pub direction: Direction, pub script: &'static str }
pub const ARABIC_SA: Locale = Locale { id: "ar-SA", language: "ar", direction: Direction::Rtl, script: "Arabic" };
pub const ENGLISH_US: Locale = Locale { id: "en-US", language: "en", direction: Direction::Ltr, script: "Latin" };
pub fn locale_for(id: &str) -> Locale {
    if id.to_ascii_lowercase().starts_with("ar") { ARABIC_SA } else { ENGLISH_US }
}

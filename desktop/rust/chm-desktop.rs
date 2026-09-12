#[derive(Clone, Copy, Debug)]
pub enum Platform { LinuxGtk, LinuxQt, WindowsWin32, WindowsModern, MacOSAppKit, MacOSSwiftUI, Classic }
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum EventType { WindowCreate, WindowClose, WindowMove, WindowResize, FocusIn, FocusOut, KeyDown, KeyUp, TextInput, PointerMove, PointerDown, PointerUp, Wheel, TouchBegin, TouchUpdate, TouchEnd, Gesture, DragBegin, DragUpdate, DragEnd, MenuCommand, DisplayChange, ThemeChange, Quit }
#[derive(Clone, Debug)]
pub struct Event { pub event_type: EventType, pub timestamp_ns:u64, pub device_id:String, pub window_id:String, pub x:f64, pub y:f64, pub dx:f64, pub dy:f64, pub modifiers:u32, pub buttons:u32, pub key:String, pub text:String }

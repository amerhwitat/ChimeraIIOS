namespace ChimeraIIOS.Desktop;

public enum DesktopPlatform { LinuxGtk, LinuxQt, WindowsWin32, WindowsModern, MacOSAppKit, MacOSSwiftUI, Classic }
public enum DesktopEventType { WindowCreate, WindowClose, WindowMove, WindowResize, FocusIn, FocusOut, KeyDown, KeyUp, TextInput, PointerMove, PointerDown, PointerUp, Wheel, TouchBegin, TouchUpdate, TouchEnd, Gesture, DragBegin, DragUpdate, DragEnd, MenuCommand, DisplayChange, ThemeChange, Quit }
public readonly record struct DesktopEvent(DesktopEventType Type, long TimestampNs, string DeviceId, string WindowId = "", double X = 0, double Y = 0, double Dx = 0, double Dy = 0, uint Modifiers = 0, uint Buttons = 0, string Key = "", string Text = "");
public sealed class EventRouter { private readonly Dictionary<DesktopEventType, Action<DesktopEvent>> handlers = new(); public void On(DesktopEventType t, Action<DesktopEvent> h) => handlers[t]=h; public void Dispatch(DesktopEvent e) { if(handlers.TryGetValue(e.Type,out var h)) h(e); } }

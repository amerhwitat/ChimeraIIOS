"""Portable Aurora desktop/event model; native backends can translate platform events into this API."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Any

class Platform(str, Enum):
    LINUX_GTK='linux-gtk'; LINUX_QT='linux-qt'; WINDOWS_WIN32='windows-win32'; WINDOWS_MODERN='windows-modern'; MACOS_APPKIT='macos-appkit'; MACOS_SWIFTUI='macos-swiftui'; CLASSIC='classic'
class EventType(str, Enum):
    WINDOW_CREATE='window_create'; WINDOW_CLOSE='window_close'; WINDOW_MOVE='window_move'; WINDOW_RESIZE='window_resize'; FOCUS_IN='focus_in'; FOCUS_OUT='focus_out'; KEY_DOWN='key_down'; KEY_UP='key_up'; TEXT_INPUT='text_input'; POINTER_MOVE='pointer_move'; POINTER_DOWN='pointer_down'; POINTER_UP='pointer_up'; WHEEL='wheel'; TOUCH_BEGIN='touch_begin'; TOUCH_UPDATE='touch_update'; TOUCH_END='touch_end'; GESTURE='gesture'; DRAG_BEGIN='drag_begin'; DRAG_UPDATE='drag_update'; DRAG_END='drag_end'; MENU_COMMAND='menu_command'; DISPLAY_CHANGE='display_change'; THEME_CHANGE='theme_change'; QUIT='quit'
@dataclass(frozen=True)
class Event:
    type: EventType; timestamp_ns: int; device_id: str; window_id: str=''; x: float=0; y: float=0; dx: float=0; dy: float=0; modifiers: int=0; buttons: int=0; key: str=''; text: str=''; payload: Dict[str,Any]=field(default_factory=dict)
class EventRouter:
    def __init__(self): self._handlers: Dict[EventType,Callable[[Event],None]]={}
    def on(self, event_type, handler): self._handlers[event_type]=handler
    def dispatch(self, event):
        handler=self._handlers.get(event.type)
        if handler: handler(event)
@dataclass(frozen=True)
class DesktopProfile:
    platform: Platform; name: str; menu_bar: bool=True; gestures: bool=True; accessibility: bool=True

def profile(platform: Platform) -> DesktopProfile:
    return DesktopProfile(platform, platform.value, platform is not Platform.CLASSIC, platform is not Platform.CLASSIC)

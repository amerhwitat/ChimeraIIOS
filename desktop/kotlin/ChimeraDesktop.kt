package chimera.desktop

enum class Platform { LINUX_GTK, LINUX_QT, WINDOWS_WIN32, WINDOWS_MODERN, MACOS_APPKIT, MACOS_SWIFTUI, CLASSIC }
enum class EventType { WINDOW_CREATE, WINDOW_CLOSE, WINDOW_MOVE, WINDOW_RESIZE, FOCUS_IN, FOCUS_OUT, KEY_DOWN, KEY_UP, TEXT_INPUT, POINTER_MOVE, POINTER_DOWN, POINTER_UP, WHEEL, TOUCH_BEGIN, TOUCH_UPDATE, TOUCH_END, GESTURE, DRAG_BEGIN, DRAG_UPDATE, DRAG_END, MENU_COMMAND, DISPLAY_CHANGE, THEME_CHANGE, QUIT }
data class Event(val type: EventType, val timestampNs: Long, val deviceId: String, val windowId: String = "", val x: Double = 0.0, val y: Double = 0.0, val dx: Double = 0.0, val dy: Double = 0.0, val modifiers: UInt = 0u, val buttons: UInt = 0u, val key: String = "", val text: String = "")
class EventRouter { private val handlers = mutableMapOf<EventType,(Event)->Unit>(); fun on(type: EventType, handler:(Event)->Unit){handlers[type]=handler}; fun dispatch(event:Event){handlers[event.type]?.invoke(event)} }

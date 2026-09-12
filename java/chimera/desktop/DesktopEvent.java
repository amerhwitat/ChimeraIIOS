package chimera.desktop;

public record DesktopEvent(Type type, long timestampNs, String deviceId, String windowId,
                           double x, double y, double dx, double dy,
                           int modifiers, int buttons, String key, String text) {
    public enum Type { WINDOW_CREATE, WINDOW_CLOSE, WINDOW_MOVE, WINDOW_RESIZE, FOCUS_IN, FOCUS_OUT,
        KEY_DOWN, KEY_UP, TEXT_INPUT, POINTER_MOVE, POINTER_DOWN, POINTER_UP, WHEEL,
        TOUCH_BEGIN, TOUCH_UPDATE, TOUCH_END, GESTURE, DRAG_BEGIN, DRAG_UPDATE, DRAG_END,
        MENU_COMMAND, DISPLAY_CHANGE, THEME_CHANGE, QUIT }
}

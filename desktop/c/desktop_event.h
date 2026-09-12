#ifndef CHM_DESKTOP_EVENT_H
#define CHM_DESKTOP_EVENT_H
#include <stdint.h>
typedef enum { CHM_LINUX_GTK, CHM_LINUX_QT, CHM_WINDOWS_WIN32, CHM_WINDOWS_MODERN, CHM_MACOS_APPKIT, CHM_MACOS_SWIFTUI, CHM_CLASSIC } chm_desktop_platform_t;
typedef enum { CHM_WINDOW_CREATE, CHM_WINDOW_CLOSE, CHM_WINDOW_MOVE, CHM_WINDOW_RESIZE, CHM_FOCUS_IN, CHM_FOCUS_OUT, CHM_KEY_DOWN, CHM_KEY_UP, CHM_TEXT_INPUT, CHM_POINTER_MOVE, CHM_POINTER_DOWN, CHM_POINTER_UP, CHM_WHEEL, CHM_TOUCH_BEGIN, CHM_TOUCH_UPDATE, CHM_TOUCH_END, CHM_GESTURE, CHM_DRAG_BEGIN, CHM_DRAG_UPDATE, CHM_DRAG_END, CHM_MENU_COMMAND, CHM_DISPLAY_CHANGE, CHM_THEME_CHANGE, CHM_QUIT } chm_desktop_event_type_t;
typedef struct { chm_desktop_event_type_t type; uint64_t timestamp_ns; const char *device_id; const char *window_id; double x,y,dx,dy; uint32_t modifiers,buttons; const char *key,*text; } chm_desktop_event_t;
#endif

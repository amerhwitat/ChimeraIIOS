#ifndef CHIMERA_WIN32_MESSAGE_H
#define CHIMERA_WIN32_MESSAGE_H

#include "chimera/event.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef chm_handle chm_hwnd;
typedef uintptr_t chm_wparam;
typedef intptr_t chm_lparam;
typedef struct chm_win32_msg {
    chm_hwnd hwnd;
    uint32_t message;
    chm_wparam wParam;
    chm_lparam lParam;
    uint64_t time_ns;
} chm_win32_msg;
typedef void (*chm_win32_wndproc)(const chm_win32_msg *message, void *context);

enum {
    CHM_WM_QUIT = 0x0012,
    CHM_WM_CLOSE = 0x0010,
    CHM_WM_KEYDOWN = 0x0100,
    CHM_WM_KEYUP = 0x0101,
    CHM_WM_MOUSEMOVE = 0x0200,
    CHM_WM_LBUTTONDOWN = 0x0201,
    CHM_WM_LBUTTONUP = 0x0202,
    CHM_WM_USER = 0x0400
};

/* Binds the calling thread to an explicitly created queue. The queue remains
 * owned by its creator; callers must unbind before destroying it. */
int chm_win32_bind_message_queue(chm_event_queue *queue);
int chm_win32_post_message(chm_hwnd hwnd, uint32_t message,
                           chm_wparam wParam, chm_lparam lParam);
int chm_win32_post_quit_message(int exit_code);
/* GetMessage: 1=message, 0=WM_QUIT, 2=timeout, -1=error. Peek: 1=message, 0=empty. */
int chm_win32_get_message(chm_win32_msg *out, uint32_t timeout_ms);
int chm_win32_peek_message(chm_win32_msg *out);
int chm_win32_dispatch_message(const chm_win32_msg *message,
                               chm_win32_wndproc procedure, void *context);

#ifdef __cplusplus
}
#endif
#endif

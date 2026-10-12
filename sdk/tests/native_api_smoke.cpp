#include "chimera/event.h"
#include "chimera/file.h"
#include "chimera/win32_message.h"
#include <cassert>
#include <cstdio>
#include <cstring>

static void count_event(const chm_event *event, void *context) {
    if (event->type == CHM_EVENT_USER) ++*static_cast<unsigned *>(context);
}
int main() {
    auto *q = chm_event_queue_create(4);
    assert(q);
    assert(CHM_PostMessage(q, 2, CHM_EVENT_USER, 11, 12) == 0);
    CHM_MSG event{};
    assert(CHM_GetMessage(q, &event, 0) == 1);
    assert(event.type == CHM_EVENT_USER && event.value1 == 11);
    unsigned count = 0;
    assert(CHM_DispatchMessage(&event, count_event, &count) == 0 && count == 1);
    assert(chm_win32_bind_message_queue(q) == 0);
    assert(chm_win32_post_message(9, CHM_WM_USER + 3, 17, 23) == 0);
    chm_win32_msg winmsg{};
    assert(chm_win32_get_message(&winmsg, 10) == 1);
    assert(winmsg.hwnd == 9 && winmsg.message == CHM_WM_USER + 3);
    assert(winmsg.wParam == 17 && winmsg.lParam == 23);
    assert(chm_win32_post_quit_message(5) == 0);
    assert(chm_win32_get_message(&winmsg, 10) == 0);
    assert(winmsg.message == CHM_WM_QUIT && winmsg.wParam == 5);
    assert(chm_win32_get_message(&winmsg, 1) == 2);
    assert(chm_win32_peek_message(&winmsg) == 0);
    assert(chm_win32_bind_message_queue(nullptr) == -1);
    chm_event_queue_destroy(q);
    const char *path = "chimera-sdk-smoke.tmp";
    chm_fd fd = chm_open(path, CHM_O_WRITE_ONLY | CHM_O_CREATE | CHM_O_TRUNCATE, 0600);
    assert(fd >= 0);
    const char data[] = "abc";
    assert(chm_write(fd, data, 3) == 3);
    assert(chm_close(fd) == 0);
    char buf[4]{};
    fd = chm_open(path, CHM_O_READ_ONLY, 0);
    assert(fd >= 0 && chm_read(fd, buf, 3) == 3);
    assert(std::strcmp(buf, "abc") == 0);
    assert(chm_close(fd) == 0 && chm_unlink(path) == 0);
    return 0;
}

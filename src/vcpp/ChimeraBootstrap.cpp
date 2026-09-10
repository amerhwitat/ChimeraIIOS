#include <windows.h>
#include <string>

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    const std::wstring message =
        L"Chimera II OS Windows bootstrapper\n"
        L"Native launcher: MSVC/Win32\n"
        L"Managed payload: .NET 8/9/10 where supported.";
    MessageBoxW(nullptr, message.c_str(), L"Chimera II OS", MB_OK | MB_ICONINFORMATION);
    return 0;
}

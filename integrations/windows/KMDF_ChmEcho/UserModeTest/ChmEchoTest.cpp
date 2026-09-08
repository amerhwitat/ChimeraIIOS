#include <windows.h>
#include <iostream>
#include <string>
#include "../Driver/chm_ioctl.h"

int main()
{
    HANDLE device = CreateFileW(L"\\\\.\\ChimeraKMDFEcho", GENERIC_READ | GENERIC_WRITE, 0,
                                nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (device == INVALID_HANDLE_VALUE) {
        std::cerr << "CreateFile failed: " << GetLastError() << "\n";
        return 1;
    }

    const std::string input = "Hello KMDF";
    char output[256]{};
    DWORD returned = 0;
    BOOL ok = DeviceIoControl(device, IOCTL_CHM_ECHO,
                              const_cast<char*>(input.data()), static_cast<DWORD>(input.size()),
                              output, sizeof(output), &returned, nullptr);
    CloseHandle(device);

    if (!ok) {
        std::cerr << "DeviceIoControl failed: " << GetLastError() << "\n";
        return 1;
    }
    std::cout.write(output, returned);
    std::cout << "\n";
    return 0;
}

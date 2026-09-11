# Native main.cpp linkage requirements

Keep the existing native application body and ensure its Windows entry point includes:

```cpp
#include <windows.h>
#include <shlobj.h>
#pragma comment(lib, "comctl32.lib")
```

The shared `windows_linkage.h` and `external_linkage.cpp` carry the same external-reference contract for the rest of the native target.

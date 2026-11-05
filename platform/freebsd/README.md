# FreeBSD host integration

The Hosted edition uses a POSIX/BSD user-space bridge on supported FreeBSD hosts. The current native service lifecycle adapter uses rc.d and sysrc through tools/hosted/chimera-host-services.py.

- Service inspection: chimera-host-services list and chimera-host-services status sshd.
- Lifecycle mutations require --apply, the confirmation phrase CHIMERA-HOST-SERVICE-CHANGE, and root privileges.
- Interface and route inspection use ifconfig and netstat.
- Static route commands from the Cisco/Junos compatibility layer are translated to the FreeBSD route utility.
- FreeBSD-specific APIs such as kqueue, PF, routing sockets and jail management require dedicated adapters; Linux netlink, systemd and Linux kernel modules are not assumed.
- BareMetal build and flash tooling is supported only when the selected LLVM/Clang, NASM and CMake toolchains are available.

FreeBSD kernel replacement, complete POSIX syscall equivalence and every FreeBSD driver are not claimed.

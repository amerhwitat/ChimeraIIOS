# Chimera II OS — Linux Commands Source Catalog and Integration Plan

Generated from a deep review of the supplied LabEx Linux Commands index and upstream source families. The LabEx index covers broad groups including file/directory operations, text processing, networking, process management, package management, scripting/programming, storage, terminal, system, and administrative commands. It is a command/learning catalog, not the canonical source repository. citeturn2search0turn2view0

## Upstream source families

| Family | Representative commands | Canonical source | License/integration note |
|---|---|---|---|
| GNU Coreutils | ls, cat, cp, mv, rm, mkdir, chmod, head, tail, sort, uniq, wc | https://www.gnu.org/software/coreutils/ | GPL; preserve upstream notices and source/build separation |
| util-linux | mount, fdisk, dmesg, lsblk, hexdump, login/terminal/system utilities | https://github.com/util-linux/util-linux | Mixed licenses by component; preserve per-file SPDX metadata |
| iproute2 | ip, ss, tc and modern network administration | https://git.kernel.org/pub/scm/network/iproute2/iproute2.git | Preserve upstream license metadata |
| net-tools | ifconfig, netstat, route and legacy networking tools | upstream net-tools project | Compatibility/reference layer; prefer modern iproute2 APIs |
| sudo | privilege transition and policy tooling | https://github.com/sudo-project/sudo | ISC; retain upstream notices |
| Bash / POSIX shells | shell language, built-ins, jobs, pipelines | Bash/OpenBSD/POSIX upstreams | Shell semantics are compatibility targets, not copied into the kernel |
| Toybox | compact multi-call userland utilities | https://github.com/landley/toybox | 0BSD; particularly useful for permissive minimal-userland components |
| Linux kernel | syscalls, scheduling, VFS, networking, drivers | https://github.com/torvalds/linux | GPL-2.0 with Linux syscall exception; do not merge kernel source wholesale into Chimera |

GNU Coreutils explicitly provides source access and a code-structure overview; current stable releases should be acquired from GNU rather than copied from a tutorial page. citeturn1search2turn1search4 util-linux is a large C project containing disk, mount, login, scheduling, terminal, text, and system utility families. citeturn0search2 Sudo publishes its source under an ISC-style license with SPDX headers in source files. citeturn0search0turn0search1 Toybox is an all-in-one Linux command line implementation under 0BSD. citeturn1search0turn1search8 The Linux kernel has separate licensing rules and must not be treated as a generic reusable code bundle. citeturn1search7turn1search12

## Chimera command families

The registry is organized into these capability domains:

1. filesystem: `ls cd pwd mkdir rmdir touch cp mv rm ln readlink find locate updatedb which whereis file stat du df tree`
2. text: `cat less more grep sed awk cut paste sort uniq tr head tail wc diff patch split join tee`
3. storage/system: `mount umount fdisk lsblk blkid dmesg hexdump od sync`
4. process: `ps top kill pkill pgrep killall nice renice jobs fg bg nohup`
5. networking: `ip ss ping traceroute route ifconfig netstat dig nslookup host ssh scp curl wget ftp telnet`
6. packages: `apt apt-get dpkg dnf yum rpm pacman zypper emerge snap flatpak`
7. shells/programming: `bash sh ksh cc gcc g++ make cmake ninja meson gdb`
8. administration: `sudo su login passwd chsh chown chmod chgrp getent id whoami`
9. compatibility/legacy: mtools, net-tools, System V/BSD/POSIX variants where legally and technically appropriate.

The catalog is intentionally broader than a single distribution. Availability is capability-based and determined at runtime by the command registry.

## Source acquisition rule

Chimera II does **not** silently copy every upstream repository into one monolithic tree. Instead it maintains:

- immutable upstream references and version metadata;
- SPDX/license manifests;
- optional vendored source trees only where licensing and maintenance permit;
- clean Chimera adapters and syscall shims;
- conformance tests against documented command behavior;
- a reproducible source acquisition script.

This prevents license contamination, duplicate implementations, and unnecessary divergence while still making the complete upstream source set reproducibly obtainable.

## Two implementations

### A. Standalone Chimera II OS

`standalone/` exposes the registry through Koronos userland, VFS, Spotnik, process management, package integration, and Aurora Terminal. Commands are implemented natively, adapted from permissively licensed components where appropriate, or built as isolated upstream packages.

### B. Aurora Web UI

`webui/` exposes the same registry through a capability-scoped HTTP/WebSocket API. The browser never receives direct host shell privileges. Each terminal session is isolated, authenticated, auditable, cancellable, and mapped to the same command capability model as the standalone OS.

## Multithreading

Parallelism is a scheduling property, not a blanket command behavior. The runtime uses CPU-aware bounded pools, async I/O, batching, work stealing only where measurable, per-session isolation, lock minimization, and deterministic serial mode. Commands whose POSIX behavior depends on ordering remain ordered. GUI operations remain on the UI thread.

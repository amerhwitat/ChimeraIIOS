#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OS=chimera
PREFIX=${PREFIX:-/usr}
SYSCONFDIR=${SYSCONFDIR:-/etc}
LIBEXECDIR=${LIBEXECDIR:-$PREFIX/libexec}
SYSTEMD_DIR=${SYSTEMD_DIR:-$PREFIX/lib/systemd/system}
DBUS_SERVICES_DIR=${DBUS_SERVICES_DIR:-$PREFIX/share/dbus-1/system-services}
DESTDIR=${DESTDIR:-}
usage() { echo "usage: $0 [--os chimera|octavian]"; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --os) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; OS=$2; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
case "$OS" in
  chimera)
    SERVICE=chimera-dbus.service
    BUS_NAME=org.chimera.OS
    UNIT_FILE=$ROOT/services/dbus/chimera-dbus.service
    POLICY_FILE=$ROOT/services/dbus/org.chimera.OS.conf
    ACTIVATION_FILE=$ROOT/services/dbus/org.chimera.OS.service
    INIT_FILE=$ROOT/services/dbus/chimera-dbus.init
    EXECDIR=$LIBEXECDIR/chimera
    ;;
  octavian)
    SERVICE=octavian-dbus.service
    BUS_NAME=org.octavian.OS
    UNIT_FILE=$ROOT/services/dbus/octavian-dbus.service
    POLICY_FILE=$ROOT/services/dbus/org.octavian.OS.conf
    ACTIVATION_FILE=$ROOT/services/dbus/org.octavian.OS.service
    INIT_FILE=$ROOT/services/dbus/octavian-dbus.init
    EXECDIR=$LIBEXECDIR/octavian
    ;;
  *) echo "invalid OS '$OS'; use chimera or octavian" >&2; exit 2 ;;
esac
put() { src=$1; dst=$2; install -D -m "$3" "$src" "$DESTDIR$dst"; }
put "$ROOT/services/dbus/chimera_dbus_service.py" "$EXECDIR/chimera_dbus_service.py" 0755
put "$UNIT_FILE" "$SYSTEMD_DIR/$SERVICE" 0644
put "$POLICY_FILE" "$SYSCONFDIR/dbus-1/system.d/$BUS_NAME.conf" 0644
put "$ACTIVATION_FILE" "$DBUS_SERVICES_DIR/$BUS_NAME.service" 0644
put "$INIT_FILE" "$SYSCONFDIR/init.d/$SERVICE" 0755
put "$ROOT/services/dbus/requirements.txt" "$PREFIX/share/$OS/dbus/requirements.txt" 0644
echo "Staged $SERVICE for $OS under ${DESTDIR:-/}; install dbus-next and reload the system bus/service manager before enabling it."

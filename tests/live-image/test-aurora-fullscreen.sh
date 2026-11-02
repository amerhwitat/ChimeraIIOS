#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <desktop-file-uri>" >&2
  exit 2
fi
uri="$1"
log_dir="$(mktemp -d)"
openbox --sm-disable >"$log_dir/openbox.log" 2>&1 &
wm_pid=$!
app_pid=""
cleanup() {
  [[ -n "$app_pid" ]] && kill "$app_pid" 2>/dev/null || true
  kill "$wm_pid" 2>/dev/null || true
  wait "$app_pid" 2>/dev/null || true
  wait "$wm_pid" 2>/dev/null || true
  rm -rf "$log_dir"
}
trap cleanup EXIT

for attempt in $(seq 1 50); do
  if xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null | grep -Eq 'window id # 0x[[:xdigit:]]+'; then
    break
  fi
  if ! kill -0 "$wm_pid" 2>/dev/null; then
    cat "$log_dir/openbox.log" >&2
    echo "Openbox exited before becoming the window manager" >&2
    exit 1
  fi
  sleep 0.1
done
xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null | grep -Eq 'window id # 0x[[:xdigit:]]+' || {
  cat "$log_dir/openbox.log" >&2
  echo "Openbox did not register as the window manager" >&2
  exit 1
}

python3 live-image/lib/aurora-kiosk.py "$uri" >"$log_dir/kiosk.log" 2>&1 &
app_pid=""
for attempt in $(seq 1 100); do
  app_pid="$(xdotool search --onlyvisible --name '^Aurora Desktop$' 2>/dev/null | head -n1 || true)"
  [[ -n "$app_pid" ]] && break
  sleep 0.1
done
if [[ -z "$app_pid" ]]; then
  cat "$log_dir/openbox.log" "$log_dir/kiosk.log" >&2
  echo "Aurora kiosk window did not appear" >&2
  exit 1
fi

state="$(xprop -id "$app_pid" _NET_WM_STATE 2>/dev/null || true)"
if ! grep -q '_NET_WM_STATE_FULLSCREEN' <<<"$state"; then
  cat "$log_dir/kiosk.log" >&2
  echo "Aurora kiosk did not enter EWMH fullscreen state: $state" >&2
  exit 1
fi

screen="$(xdpyinfo | awk '/dimensions:/{print $2; exit}')"
expected_w="${screen%x*}"
expected_h="${screen#*x}"
info="$(xwininfo -id "$app_pid")"
actual_w="$(awk '/Width:/{print $2; exit}' <<<"$info")"
actual_h="$(awk '/Height:/{print $2; exit}' <<<"$info")"
actual_x="$(awk '/Absolute upper-left X:/{print $4; exit}' <<<"$info")"
actual_y="$(awk '/Absolute upper-left Y:/{print $4; exit}' <<<"$info")"
if [[ "$actual_w" != "$expected_w" || "$actual_h" != "$expected_h" || "$actual_x" != "0" || "$actual_y" != "0" ]]; then
  cat "$log_dir/kiosk.log" >&2
  echo "Aurora desktop is not fullscreen: screen=$screen window=${actual_w}x${actual_h}+${actual_x}+${actual_y}" >&2
  exit 1
fi
grep -Fq "display=$screen" "$log_dir/kiosk.log"
echo "Aurora fullscreen passed: $screen"

#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
BUILD_DIR="${CHIMERA_BUILD_DIR:-/mnt/d/chimera-build}"
JOBS="${CHIMERA_JOBS:-$(nproc 2>/dev/null || echo 4)}"
LOG_DIR="${BUILD_DIR}/logs/koronos-orchestrator"
STATE_DIR="${BUILD_DIR}/.koronos-state"
LOCK_FILE="${BUILD_DIR}/.koronos-build.lock"

mkdir -p "$LOG_DIR" "$STATE_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "[ERROR] Another Koronos/Chimera orchestrator is already running: $LOCK_FILE" >&2
    exit 20
fi

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

[[ -d "$ROOT" ]] || die "Missing source tree: $ROOT"
[[ -d "$ROOT/tools" ]] || die "Missing tools directory: $ROOT/tools"

run_step() {
    local name="$1"; shift
    local log_file="$LOG_DIR/${name}.log"
    local stamp="$STATE_DIR/${name}.ok"

    log "START $name"
    rm -f "$stamp"

    set +e
    "$@" > >(tee "$log_file") 2>&1
    local rc=$?
    set -e

    if (( rc != 0 )); then
        log "FAIL  $name (rc=$rc) -- see $log_file"
        return "$rc"
    fi

    touch "$stamp"
    log "DONE  $name"
}

parallel_group() {
    local -a pids=()
    local -a names=()
    local name cmd pid rc failed=0

    while (( $# )); do
        name="$1"; shift
        cmd="$1"; shift
        names+=("$name")
        log "PARALLEL START $name"
        bash -lc "$cmd" > >(tee "$LOG_DIR/${name}.log") 2>&1 &
        pid=$!
        pids+=("$pid")
    done

    for i in "${!pids[@]}"; do
        if wait "${pids[$i]}"; then
            touch "$STATE_DIR/${names[$i]}.ok"
            log "PARALLEL DONE ${names[$i]}"
        else
            rc=$?
            log "PARALLEL FAIL ${names[$i]} (rc=$rc)"
            failed=1
        fi
    done

    (( failed == 0 )) || return 1
}

# ------------------------------------------------------------
# Stage 0: validate scripts before starting concurrent work.
# ------------------------------------------------------------
log "=== KORONOS DEPENDENCY-AWARE BUILD ==="
log "ROOT=$ROOT"
log "BUILD_DIR=$BUILD_DIR"
log "PARALLEL_JOBS=$JOBS"

for f in \
    "$ROOT/tools/fetch-foreign-runtimes.sh" \
    "$ROOT/tools/build-live-boot-binaries.sh" \
    "$ROOT/tools/build-boot-artifacts.sh" \
    "$ROOT/iso/chimera-live-iso.sh" \
    "$ROOT/build-chimera-iso.sh"; do
    if [[ -f "$f" ]]; then
        bash -n "$f" || die "Syntax error: $f"
    fi
done

# ------------------------------------------------------------
# Stage 1: independent prerequisites run in parallel.
# Foreign runtimes do not depend on the Koronos ELF itself.
# ------------------------------------------------------------
if [[ -f "$ROOT/tools/fetch-foreign-runtimes.sh" ]]; then
    parallel_group \
      "foreign-runtimes" "cd '$ROOT' && bash '$ROOT/tools/fetch-foreign-runtimes.sh'" \
      || die "Independent prerequisite stage failed."
else
    log "SKIP foreign-runtimes: script not present."
fi

# ------------------------------------------------------------
# Stage 2: Koronos kernel. Everything consuming the ELF waits for it.
# ------------------------------------------------------------
if [[ -x "$ROOT/kernel/build-koronos.sh" ]]; then
    run_step "koronos-kernel" bash "$ROOT/kernel/build-koronos.sh" \
      || die "Koronos kernel build failed."
elif [[ -f "$ROOT/kernel/build-koronos.sh" ]]; then
    run_step "koronos-kernel" bash "$ROOT/kernel/build-koronos.sh" \
      || die "Koronos kernel build failed."
else
    die "Koronos build script not found: $ROOT/kernel/build-koronos.sh"
fi

KORONOS="$ROOT/build/koronos/x86_64/koronos.elf"
[[ -f "$KORONOS" ]] || die "Koronos ELF was not produced: $KORONOS"

# ------------------------------------------------------------
# Stage 3: direct consumers of Koronos. These are related and are
# intentionally sequential to prevent shared-output races.
# ------------------------------------------------------------
run_step "boot-artifacts" bash "$ROOT/tools/build-boot-artifacts.sh" \
    || die "Boot artifact generation failed."

run_step "live-boot" bash "$ROOT/tools/build-live-boot-binaries.sh" \
    || die "Live-boot generation failed."

# ------------------------------------------------------------
# Stage 4a: Aurora Applications/menu generation. This runs after the
# application/rootfs payload exists and before ISO mastering so all
# discovered terminal applications are captured in Aurora.
# ------------------------------------------------------------
if [[ -x "$ROOT/tools/aurora/generate-applications-menu.sh" ]]; then
    run_step "aurora-applications-menu" bash "$ROOT/tools/aurora/generate-applications-menu.sh" \
        || die "Aurora Applications/menu generation failed."
fi

# ------------------------------------------------------------
# Stage 4: independent post-Koronos tasks may run together, but only
# after the canonical Koronos + boot artifacts exist.
# ------------------------------------------------------------
POST_CMDS=()
POST_NAMES=()

if [[ -x "$ROOT/iso/chimera-live-iso.sh" ]]; then
    POST_NAMES+=("live-iso")
    POST_CMDS+=("cd '$ROOT' && bash '$ROOT/iso/chimera-live-iso.sh'")
elif [[ -f "$ROOT/iso/chimera-live-iso.sh" ]]; then
    POST_NAMES+=("live-iso")
    POST_CMDS+=("cd '$ROOT' && bash '$ROOT/iso/chimera-live-iso.sh'")
fi

if [[ -x "$ROOT/build-chimera-iso.sh" ]]; then
    POST_NAMES+=("full-iso")
    POST_CMDS+=("cd '$ROOT' && bash '$ROOT/build-chimera-iso.sh'")
elif [[ -f "$ROOT/build-chimera-iso.sh" ]]; then
    POST_NAMES+=("full-iso")
    POST_CMDS+=("cd '$ROOT' && bash '$ROOT/build-chimera-iso.sh'")
fi

if (( ${#POST_CMDS[@]} )); then
    # These two are deliberately NOT run simultaneously if they both write
    # the same ISO/staging directory. Serialize them unless the caller has
    # explicitly opted into isolated output directories.
    if [[ "${CHIMERA_ISOLATED_ISO_BUILDS:-0}" == "1" && ${#POST_CMDS[@]} -gt 1 ]]; then
        args=()
        for i in "${!POST_CMDS[@]}"; do
            args+=("${POST_NAMES[$i]}" "${POST_CMDS[$i]}")
        done
        parallel_group "${args[@]}" || die "Parallel ISO stage failed."
    else
        for i in "${!POST_CMDS[@]}"; do
            run_step "${POST_NAMES[$i]}" bash -lc "${POST_CMDS[$i]}" \
                || die "${POST_NAMES[$i]} failed."
        done
    fi
fi

# ------------------------------------------------------------
# Final integrity gate.
# ------------------------------------------------------------
log "=== FINAL INTEGRITY CHECK ==="

[[ -s "$KORONOS" ]] || die "Koronos ELF missing/empty after build."

if [[ -f "$BUILD_DIR/live-boot/boot/koronos/koronos.elf" ]]; then
    LIVE_KORONOS="$BUILD_DIR/live-boot/boot/koronos/koronos.elf"
    if [[ "$(realpath -m -- "$KORONOS")" == "$(realpath -m -- "$LIVE_KORONOS")" ]]; then
        log "Koronos live-boot artifact shares the canonical ELF path; no copy required."
    else
        cmp -s -- "$KORONOS" "$LIVE_KORONOS" || die "Live-boot Koronos artifact differs from canonical ELF."
        log "Koronos live-boot artifact verified."
    fi
fi

if [[ -f "$BUILD_DIR/boot-artifacts/koronos/koronos.elf" ]]; then
    cmp -s -- "$KORONOS" "$BUILD_DIR/boot-artifacts/koronos/koronos.elf" \
        || die "Boot-artifacts Koronos ELF differs from canonical ELF."
    log "Boot-artifacts Koronos ELF verified."
fi

log "=== BUILD COMPLETE ==="
log "Canonical Koronos: $KORONOS"
log "Logs: $LOG_DIR"

  for f in \
    boot.png desktop.png showcase.png menus/default.png \
    splash/aurora-splash.png installer/aurora-installer.png \
    recovery/aurora-recovery.png diagnostics/aurora-diagnostics.png \
    live/aurora-live.png mobile/aurora-mobile.png; do
    [[ -s "$visual/$f" ]] || continue
    cp -f "$visual/$f" "$ISO_DIR/boot/visual/$(basename "$f")"
  done

  # Canonical GRUB/Jasper background: materialize the repository's embedded
  # artwork when available, otherwise use the generated Aurora boot artwork.
  # Decode the optional embedded GRUB artwork defensively. Some WSL/base64
  # implementations reject otherwise usable payloads because of whitespace or
  # padding differences. A bad optional payload must never abort branding.
  local embedded_art="$SCRIPT_DIR/boot/visual/aurora-wayland-glass.jpg.b64"
  local embedded_out="$ISO_DIR/boot/visual/aurora-wayland-glass.jpg"
  if [[ -s "$embedded_art" ]]; then
    if base64 -d -i "$embedded_art" > "$embedded_out.tmp" 2>"$LOG_DIR/aurora-artwork-base64.log" &&
       [[ -s "$embedded_out.tmp" ]] &&
       { head -c 2 "$embedded_out.tmp" | cmp -s - <(printf '\\xff\\xd8') || head -c 8 "$embedded_out.tmp" | cmp -s - <(printf '\\x89PNG\\r\\n\\x1a\\n'); }; then
      mv -f "$embedded_out.tmp" "$embedded_out"
      log_info "Embedded Aurora GRUB artwork decoded successfully."
    else
      rm -f "$embedded_out.tmp"
      log_warning "Embedded Aurora GRUB artwork payload is invalid; using generated Aurora artwork instead."
    fi
  fi
  if [[ ! -s "$embedded_out" ]] && [[ -s "$visual/backgrounds/boot.png" ]]; then
    if command -v convert >/dev/null 2>&1; then
      if convert "$visual/backgrounds/boot.png" -quality 90 "$embedded_out" 2>"$LOG_DIR/aurora-artwork-convert.log"; then
        log_info "Generated Aurora GRUB artwork converted to JPEG."
      else
        rm -f "$embedded_out"
        log_warning "ImageMagick conversion unavailable; GRUB artwork will use the PNG fallback."
      fi
    else
      # GRUB's required raster contract is already satisfied by aurora-boot.png.
      log_warning "ImageMagick unavailable; skipping optional JPEG artwork."
    fi
  fi

  # Init.mp4 is a hardcoded offline Aurora splash asset. GRUB does not
  # decode MP4; Jasper/Wayland hands it to Aurora after the graphical session
  # is ready. The same binary is deliberately staged for installer + desktop
  # so all entry paths share one deterministic video.
  local init_video=""
  for candidate in \
    "$SCRIPT_DIR/desktop/aurora/assets/Init.mp4" \
    "$SCRIPT_DIR/desktop/aurora/assets/library/Init.mp4" \
    "$SCRIPT_DIR/build/aurora-media/Init.mp4" \
    "$SCRIPT_DIR/Init.mp4"; do
    if [[ -s "$candidate" ]]; then init_video="$candidate"; break; fi
  done

  [[ -n "$init_video" ]] || {
    log_error "Required Aurora Init.mp4 is missing."
    log_error "Expected desktop/aurora/assets/Init.mp4 or desktop/aurora/assets/library/Init.mp4."
    return 1
  }

  if command -v ffprobe >/dev/null 2>&1; then
    ffprobe -v error -select_streams v:0 -show_entries stream=codec_type \
      -of csv=p=0 "$init_video" >/dev/null || {
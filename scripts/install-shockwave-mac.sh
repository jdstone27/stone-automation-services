#!/usr/bin/env bash
#
# Install Shockwave (github.com/stephengpope/shockwave) on macOS.
#
# Downloads the latest Shockwave-mac.dmg release asset, copies Shockwave.app
# into /Applications, removes the Gatekeeper quarantine flag, and launches it.
#
# Usage:  ./scripts/install-shockwave-mac.sh
#
set -euo pipefail

REPO="stephengpope/shockwave"
ASSET="Shockwave-mac.dmg"
URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"
APP="/Applications/Shockwave.app"

WORKDIR=""
MNT=""

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

cleanup() {
  # Always detach the image, even if a later step fails, so we don't leave a
  # stale volume mounted.
  if [[ -n "$MNT" && -d "$MNT" ]]; then
    hdiutil detach "$MNT" -quiet 2>/dev/null \
      || hdiutil detach "$MNT" -force -quiet 2>/dev/null \
      || warn "could not detach $MNT; detach it manually"
  fi
  [[ -n "$WORKDIR" && -d "$WORKDIR" ]] && rm -rf "$WORKDIR"
}
trap cleanup EXIT

# --- 0. Preflight ------------------------------------------------------------
[[ "$(uname -s)" == "Darwin" ]] || die "this installer only runs on macOS (found $(uname -s))"

if pgrep -xq "Shockwave"; then
  die "Shockwave is currently running. Quit it first, then re-run this script."
fi

if [[ -e "$APP" ]]; then
  warn "$APP already exists and will be replaced."
  read -r -p "Continue? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || die "aborted by user"
fi

WORKDIR="$(mktemp -d)"
DMG="${WORKDIR}/${ASSET}"
MNT="${WORKDIR}/mnt"

# --- 1. Download -------------------------------------------------------------
log "Downloading ${ASSET} from the latest ${REPO} release"
curl -fL --retry 3 --retry-delay 2 --progress-bar -o "$DMG" "$URL" \
  || die "download failed — check your network, or that the release still publishes ${ASSET}"

[[ -s "$DMG" ]] || die "downloaded file is empty"

# A 404 or an HTML error page would still be a "successful" download of the
# wrong bytes, so confirm this is really a disk image before mounting it.
if ! file -b "$DMG" | grep -qiE 'disk image|zlib|bzip2|udif'; then
  die "downloaded file is not a disk image (got: $(file -b "$DMG"))"
fi
log "Downloaded $(du -h "$DMG" | cut -f1) to $DMG"

# --- 2. Mount, copy, unmount -------------------------------------------------
log "Mounting disk image"
mkdir -p "$MNT"
hdiutil attach "$DMG" -mountpoint "$MNT" -nobrowse -readonly -quiet \
  || die "failed to mount $DMG"

SRC="${MNT}/Shockwave.app"
[[ -d "$SRC" ]] || die "Shockwave.app not found on the mounted image (contents: $(find "$MNT" -maxdepth 1 -mindepth 1 -exec basename {} \; | tr '\n' ' '))"

log "Copying Shockwave.app to /Applications"
# ditto preserves extended attributes, symlinks and resource forks correctly;
# cp -R can mangle bundles in ways that break code signatures.
rm -rf "$APP"
ditto "$SRC" "$APP" || die "copy to /Applications failed (permission issue? try: sudo $0)"

log "Unmounting disk image"
hdiutil detach "$MNT" -quiet || hdiutil detach "$MNT" -force -quiet
MNT=""   # already detached; don't retry in cleanup

# --- 3. Clear the Gatekeeper quarantine flag ---------------------------------
# `xattr -dr com.apple.quarantine` removes exactly the quarantine attribute.
# `xattr -cr` would strip *every* extended attribute on the bundle, which is
# broader than needed and can discard metadata the app relies on.
log "Clearing the quarantine flag"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

if xattr -pr com.apple.quarantine "$APP" 2>/dev/null | grep -q .; then
  warn "quarantine attribute still present on some files"
else
  log "Quarantine flag cleared"
fi

# Report the signing status so it is clear what Gatekeeper check is being
# bypassed here.
if codesign -dv "$APP" 2>&1 | grep -q 'Authority=Developer ID'; then
  log "App carries a Developer ID signature"
else
  warn "App is not Developer ID signed — you are bypassing Gatekeeper verification."
  warn "Only proceed if you trust ${REPO}."
fi

# --- 4. Launch ---------------------------------------------------------------
log "Launching Shockwave"
open "$APP" || die "failed to launch $APP"

log "Done. Shockwave is installed at $APP"

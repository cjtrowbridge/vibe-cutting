#!/bin/sh

set -eu

PIXI_VERSION="0.72.0"
MINIMUM_GIT_VERSION="2.31.0"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TOOLS_ROOT=${VIBE_CUTTING_TOOLS_ROOT:-"$REPO_ROOT/.tools"}
MANIFEST="$SCRIPT_DIR/pixi.toml"
CHECKSUMS="$SCRIPT_DIR/checksums/pixi-v$PIXI_VERSION.sha256"
ALLOW_DOWNLOADS=0

fail() {
    printf 'vibe-cutting bootstrap: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: setup/bootstrap.sh [--allow-downloads] <doctor|setup|verify|repair|report|run> [arguments]

Examples:
  ./setup/bootstrap.sh doctor
  ./setup/bootstrap.sh --allow-downloads setup
  ./setup/bootstrap.sh run -- scripts/laser_build.py --help
EOF
}

case "$TOOLS_ROOT" in
    "$REPO_ROOT"/*) ;;
    *) fail "tools root must remain inside the repository: $TOOLS_ROOT" ;;
esac

EXISTING_ANCESTOR=$TOOLS_ROOT
while [ ! -e "$EXISTING_ANCESTOR" ]; do
    EXISTING_ANCESTOR=$(dirname -- "$EXISTING_ANCESTOR")
done
RESOLVED_ANCESTOR=$(CDPATH= cd -- "$EXISTING_ANCESTOR" && pwd -P)
case "$RESOLVED_ANCESTOR" in
    "$REPO_ROOT"|"$REPO_ROOT"/*) ;;
    *) fail "tools root resolves outside the repository: $TOOLS_ROOT" ;;
esac

if [ "${1:-}" = "--allow-downloads" ]; then
    ALLOW_DOWNLOADS=1
    shift
fi

COMMAND=${1:-}
[ -n "$COMMAND" ] || {
    usage
    exit 2
}
shift

version_at_least() {
    awk -v actual="$1" -v required="$2" 'BEGIN {
        split(actual, a, "."); split(required, r, ".");
        for (i = 1; i <= 3; i++) {
            av = (a[i] == "" ? 0 : a[i]) + 0;
            rv = (r[i] == "" ? 0 : r[i]) + 0;
            if (av > rv) exit 0;
            if (av < rv) exit 1;
        }
        exit 0;
    }'
}

verify_git() {
    command -v git >/dev/null 2>&1 || fail "Git $MINIMUM_GIT_VERSION or newer is required"
    GIT_VERSION=$(git --version | awk '{print $3}')
    version_at_least "$GIT_VERSION" "$MINIMUM_GIT_VERSION" ||
        fail "Git $GIT_VERSION is too old; Git $MINIMUM_GIT_VERSION or newer is required"
}

detect_platform() {
    OS=$(uname -s 2>/dev/null || printf unknown)
    ARCH=$(uname -m 2>/dev/null || printf unknown)
    case "$OS:$ARCH" in
        Linux:x86_64|Linux:amd64)
            PLATFORM="linux-x86_64"
            PIXI_ASSET="pixi-x86_64-unknown-linux-musl"
            ;;
        Linux:aarch64|Linux:arm64)
            PLATFORM="linux-aarch64"
            PIXI_ASSET="pixi-aarch64-unknown-linux-musl"
            ;;
        Darwin:x86_64|Darwin:amd64)
            PLATFORM="macos-x86_64"
            PIXI_ASSET="pixi-x86_64-apple-darwin"
            ;;
        Darwin:arm64|Darwin:aarch64)
            PLATFORM="macos-aarch64"
            PIXI_ASSET="pixi-aarch64-apple-darwin"
            ;;
        *) fail "unsupported platform: $OS $ARCH" ;;
    esac
    PIXI_URL="https://github.com/prefix-dev/pixi/releases/download/v$PIXI_VERSION/$PIXI_ASSET"
}

sha256_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    elif command -v openssl >/dev/null 2>&1; then
        openssl dgst -sha256 "$1" | awk '{print $NF}'
    else
        fail "no SHA-256 verifier found; install sha256sum, shasum, or openssl"
    fi
}

expected_sha256() {
    awk -v asset="$PIXI_ASSET" '$2 == asset {print $1}' "$CHECKSUMS"
}

download_file() {
    url=$1
    destination=$2
    if command -v curl >/dev/null 2>&1; then
        curl -fL --proto '=https' --tlsv1.2 "$url" -o "$destination"
    elif command -v wget >/dev/null 2>&1; then
        wget --https-only -O "$destination" "$url"
    else
        fail "no HTTPS downloader found; install curl or wget"
    fi
}

configure_pixi() {
    mkdir -p "$TOOLS_ROOT/config" "$TOOLS_ROOT/cache/pixi" "$TOOLS_ROOT/environments" \
        "$TOOLS_ROOT/logs" "$TOOLS_ROOT/reports/host-readiness" "$TOOLS_ROOT/staging" "$TOOLS_ROOT/tmp"
    PIXI_CONFIG_PATH="$TOOLS_ROOT/config/pixi.toml"
    cat >"$PIXI_CONFIG_PATH" <<EOF
detached-environments = "$TOOLS_ROOT/environments"

[cache]
root = "$TOOLS_ROOT/cache/pixi"
detached-environments = "$TOOLS_ROOT/environments"
netfs-redirect = "never"
EOF
    activate_pixi
}

activate_pixi() {
    PIXI_CONFIG_PATH="$TOOLS_ROOT/config/pixi.toml"
    [ -f "$PIXI_CONFIG_PATH" ] || fail "managed Pixi configuration is missing; run setup first"
    export PIXI_HOME="$TOOLS_ROOT/pixi-home"
    export PIXI_CACHE_DIR="$TOOLS_ROOT/cache/pixi"
    export PIXI_CONFIG_FILE="$PIXI_CONFIG_PATH"
    export PIXI_CACHE_DETACHED_ENVIRONMENTS_DIR="$TOOLS_ROOT/environments"
    export PIXI_CACHE_NETFS_REDIRECT="never"
    export VIBE_CUTTING_REPO_ROOT="$REPO_ROOT"
    export VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT"
    export VIBE_CUTTING_PIXI_VERSION="$PIXI_VERSION"
}

verify_manager() {
    PIXI_BIN="$TOOLS_ROOT/bin/pixi"
    [ -f "$PIXI_BIN" ] || return 1
    expected=$(expected_sha256)
    [ -n "$expected" ] || fail "no checksum recorded for $PIXI_ASSET"
    actual=$(sha256_file "$PIXI_BIN")
    [ "$actual" = "$expected" ] || fail "installed Pixi checksum mismatch: expected $expected, got $actual"
    [ -x "$PIXI_BIN" ] || fail "installed Pixi is not executable: $PIXI_BIN"
}

install_manager() {
    if verify_manager; then
        return
    fi
    [ "$ALLOW_DOWNLOADS" -eq 1 ] ||
        fail "Pixi is not installed; rerun with --allow-downloads after approving the pinned download"
    mkdir -p "$TOOLS_ROOT/bin" "$TOOLS_ROOT/staging"
    staged="$TOOLS_ROOT/staging/$PIXI_ASSET.part"
    rm -f "$staged"
    download_file "$PIXI_URL" "$staged"
    expected=$(expected_sha256)
    [ -n "$expected" ] || fail "no checksum recorded for $PIXI_ASSET"
    actual=$(sha256_file "$staged")
    if [ "$actual" != "$expected" ]; then
        rm -f "$staged"
        fail "downloaded Pixi checksum mismatch: expected $expected, got $actual"
    fi
    chmod 755 "$staged"
    mv "$staged" "$TOOLS_ROOT/bin/pixi"
    verify_manager
}

run_stage_two() {
    activate_pixi
    PIXI_BIN="$TOOLS_ROOT/bin/pixi"
    [ -x "$PIXI_BIN" ] || fail "managed Pixi is unavailable; run setup first"
    "$PIXI_BIN" run --manifest-path "$MANIFEST" --as-is -- python "$SCRIPT_DIR/bootstrap_host.py" "$@"
}

verify_git
detect_platform

case "$COMMAND" in
    doctor)
        manager_state="missing"
        if verify_manager; then
            manager_state="ready"
        fi
        printf 'platform=%s\n' "$PLATFORM"
        printf 'git=%s\n' "$GIT_VERSION"
        printf 'pixi=%s\n' "$manager_state"
        printf 'tools_root=%s\n' "$TOOLS_ROOT"
        ;;
    setup)
        install_manager
        if [ ! -f "$TOOLS_ROOT/state/base-ready.json" ] && [ "$ALLOW_DOWNLOADS" -ne 1 ]; then
            fail "base environment is not ready; rerun with --allow-downloads after approving dependency downloads"
        fi
        configure_pixi
        "$TOOLS_ROOT/bin/pixi" install --manifest-path "$MANIFEST" --locked
        run_stage_two setup "$@"
        ;;
    repair)
        install_manager
        [ "$ALLOW_DOWNLOADS" -eq 1 ] ||
            fail "repair may download locked dependencies; rerun with --allow-downloads after approval"
        configure_pixi
        "$TOOLS_ROOT/bin/pixi" install --manifest-path "$MANIFEST" --locked
        run_stage_two repair "$@"
        ;;
    verify|report)
        verify_manager || fail "managed Pixi is unavailable; run setup first"
        run_stage_two "$COMMAND" "$@"
        ;;
    run)
        verify_manager || fail "managed Pixi is unavailable; run setup first"
        [ "${1:-}" = "--" ] || fail "run requires -- before the repository command"
        shift
        run_stage_two run -- "$@"
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        usage >&2
        fail "unknown command: $COMMAND"
        ;;
esac

#!/bin/sh

set -eu

CONF_FLAGS=''

add_flag() {
  add=$*
  CONF_FLAGS="$CONF_FLAGS $add"
}

add_library_path() {
  add=$*
  LIBRARY_PATH="${LIBRARY_PATH:-}:$add"
  export LIBRARY_PATH
}

conf_linux() {
  cross=".ci/cross/${HOST:-nonexistent}"
  if [ -f "$cross" ]; then
    add_flag --cross-file "$cross"
  fi
  add_flag -Dminiupnpc=auto -Duml=true
}

conf_windows() {
  add_flag -Dminiupnpc=auto "$@"
}

conf_macos() {
  add_flag -Dminiupnpc=auto "$@"
  openssl=$(brew --prefix openssl)
  export PKG_CONFIG_PATH="$openssl/lib/pkgconfig"
}

case "$(uname -s)" in
Linux) conf_linux "$@" ;;
MINGW*) conf_windows "$@" ;;
Darwin) conf_macos "$@" ;;
*) exit 1 ;;
esac

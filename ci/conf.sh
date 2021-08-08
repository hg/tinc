#!/bin/sh

set -eu

conf_linux() {
  . /etc/os-release

  if type rpm >/dev/null 2>&1; then
    # CentOS 7 has OpenSSL 1.1 installed in a non-default location.
    if [ -d /usr/include/openssl11 ]; then
      set -- "$@" --with-openssl-include=/usr/include/openssl11
    fi

    if [ -d /usr/lib64/openssl11 ]; then
      set -- "$@" --with-openssl-lib=/usr/lib64/openssl11
    fi

    # RHEL 8 does not ship miniupnpc.
    if rpm -q miniupnpc-devel >/dev/null 2>&1; then
      set -- "$@" --enable-miniupnpc
    fi
  else
    if [ "$ID" != debian ] || [ "$VERSION_ID" -lt 11 ]; then
      # No vde2 in RHEL-based distributions; Debian 11 misses required header.
      set -- "$@" --enable-vde
    fi
  fi

  # Cross-compilation.
  if [ -n "${HOST:-}" ]; then
    case "$HOST" in
    armhf) triplet=arm-linux-gnueabihf ;;
    mips) triplet=mips-linux-gnu ;;
    *) exit 1 ;;
    esac

    set -- "$@" --host="$triplet"
  fi

  echo "--enable-uml $*"
}

conf_windows() {
  echo --enable-miniupnpc --disable-readline --with-curses-include=/mingw64/include/ncurses "$@"
}

conf_macos() {
  echo --with-openssl="$(brew --prefix openssl)" --with-miniupnpc="$(brew --prefix miniupnpc)" --enable-tunemu --enable-miniupnpc "$@"
}

case "$(uname -s)" in
Linux) conf_linux "$@" ;;
MINGW*) conf_windows "$@" ;;
Darwin) conf_macos "$@" ;;
*) exit 1 ;;
esac

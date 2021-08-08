#!/bin/sh

set -eu

deps_alpine() {
  apk upgrade

  apk add \
    git binutils make autoconf automake gcc linux-headers diffutils texinfo \
    procps socat shadow sudo openssl-dev zlib-dev lzo-dev ncurses-dev \
    readline-dev musl-dev lz4-dev vde2-dev
}

deps_debian() {
  ARCH=${ARCH:-}
  export DEBIAN_FRONTEND=noninteractive

  if [ -n "$ARCH" ]; then
    dpkg --add-architecture "$ARCH"
  fi

  apt-get update
  apt-get upgrade -y

  apt-get install -y \
    git binutils make autoconf automake gcc diffutils sudo texinfo netcat procps socat \
    zlib1g-dev:"$ARCH" \
    libssl-dev:"$ARCH" \
    liblzo2-dev:"$ARCH" \
    liblz4-dev:"$ARCH" \
    libncurses-dev:"$ARCH" \
    libreadline-dev:"$ARCH" \
    libgcrypt-dev:"$ARCH" \
    libminiupnpc-dev:"$ARCH" \
    libvdeplug-dev:"$ARCH" \
    "$@"

  if [ -n "$ARCH" ]; then
    apt-get install -y crossbuild-essential-"$ARCH" qemu-user
  fi
}

deps_rhel() {
  if [ "$ID" != fedora ]; then
    yum install -y epel-release

    if type dnf; then
      dnf install -y 'dnf-command(config-manager)'
      dnf config-manager --enable powertools
    fi
  fi

  yum upgrade -y

  yum install -y \
    git binutils make autoconf automake gcc diffutils sudo texinfo netcat procps systemd \
    findutils socat lzo-devel zlib-devel lz4-devel ncurses-devel readline-devel "$@"

  yum install -y openssl11-devel ||
    yum install -y openssl-devel

  # RHEL 8 does not ship miniupnpc
  yum install -y miniupnpc-devel || true
}

deps_linux() {
  . /etc/os-release

  case "$ID" in
  alpine) deps_alpine "$@" ;;
  debian | ubuntu) deps_debian "$@" ;;
  centos | almalinux | fedora) deps_rhel "$@" ;;
  *) exit 1 ;;
  esac
}

deps_macos() {
  brew install coreutils netcat automake lzo lz4 miniupnpc "$@"
  pip3 install --user compiledb
}

case "$(uname -s)" in
Linux) deps_linux "$@" ;;
Darwin) deps_macos "$@" ;;
*) exit 1 ;;
esac

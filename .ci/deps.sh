#!/bin/sh

set -eu

deps_linux_alpine() {
  apk upgrade

  apk add \
    git binutils meson pkgconf gcc linux-headers diffutils \
    procps socat shadow sudo libgcrypt-dev texinfo gzip \
    openssl-dev zlib-dev lzo-dev ncurses-dev readline-dev musl-dev lz4-dev vde2-dev
}

deps_linux_debian_mingw() {
  apt-get install -y \
    mingw-w64 mingw-w64-tools \
    wine wine-binfmt \
    libgcrypt-mingw-w64-dev \
    "$@"
}

deps_linux_debian_linux() {
  if [ -n "$HOST" ]; then
    dpkg --add-architecture "$HOST"
  fi

  apt-get update

  apt-get install -y \
    binutils make gcc \
    zlib1g-dev:"$HOST" \
    libssl-dev:"$HOST" \
    liblzo2-dev:"$HOST" \
    liblz4-dev:"$HOST" \
    libncurses-dev:"$HOST" \
    libreadline-dev:"$HOST" \
    libgcrypt-dev:"$HOST" \
    libminiupnpc-dev:"$HOST" \
    libvdeplug-dev:"$HOST" \
    "$@"

  if [ -n "$HOST" ]; then
    apt-get install -y crossbuild-essential-"$HOST" qemu-user
  else
    linux_openssl3
  fi
}

deps_linux_debian() {
  export DEBIAN_FRONTEND=noninteractive

  apt-get update
  apt-get upgrade -y
  apt-get install -y git pkgconf diffutils sudo texinfo \
    netcat-openbsd procps socat

  HOST=${HOST:-}
  if [ "$HOST" = mingw ]; then
    deps_linux_debian_mingw "$@"
  else
    deps_linux_debian_linux "$@"
  fi

  . /etc/os-release

  if [ "${ID:-}/${VERSION_CODENAME:-}" = debian/buster ]; then
    apt-get install -y python3 python3-pip ninja-build
    pip3 install meson
  else
    apt-get install -y meson
  fi
}

deps_linux_rhel() {
  if [ "$ID" != fedora ]; then
    yum install -y epel-release

    if type dnf; then
      dnf install -y 'dnf-command(config-manager)'
      dnf config-manager --enable powertools
    fi
  fi

  yum upgrade -y

  yum install -y \
    git binutils make meson pkgconf gcc diffutils sudo texinfo-tex netcat procps systemd perl-IPC-Cmd \
    findutils socat lzo-devel zlib-devel lz4-devel ncurses-devel readline-devel libgcrypt-devel "$@"

  if yum info openssl11-devel; then
    yum install -y openssl11-devel
  else
    dnf install -y openssl-devel
  fi

  if yum info miniupnpc-devel; then
    yum install -y miniupnpc-devel
  fi
}

linux_openssl3() {
  src=/usr/local/src/openssl
  ssl3=/opt/ssl3

  mkdir -p $src

  git clone --depth 1 --branch openssl-3.0.2 https://github.com/openssl/openssl $src
  cd $src

  ./Configure --prefix=$ssl3 --openssldir=$ssl3
  make -j"$(nproc)"
  make install_sw

  ldconfig -v $ssl3/lib64

  cd -
}

deps_linux() {
  . /etc/os-release

  case "$ID" in
  alpine)
    deps_linux_alpine "$@"
    ;;

  debian | ubuntu)
    deps_linux_debian "$@"
    ;;

  centos | almalinux | fedora)
    deps_linux_rhel "$@"
    linux_openssl3
    ;;

  *) exit 1 ;;
  esac
}

deps_macos() {
  brew install coreutils netcat lzo lz4 miniupnpc libgcrypt openssl meson "$@"
  pip3 install --user compiledb
}

case "$(uname -s)" in
Linux) deps_linux "$@" ;;
Darwin) deps_macos "$@" ;;
*) exit 1 ;;
esac

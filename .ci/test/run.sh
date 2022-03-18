#!/bin/sh

set -eu

bail() {
  echo >&2 "@"
  exit 1
}

header() {
  echo '################################################################################'
  echo "# $*"
  echo '################################################################################'
}

run_tests() {
  flavor="$1"
  shift

  header "Cleaning up leftovers from previous runs"

  for name in tinc tincd; do
    sudo pkill -TERM -x "$name" || true
    sudo pkill -KILL -x "$name" || true
  done

  sudo git clean -dfx
  sudo chown -R "${USER:-$(whoami)}" .

  mkdir -p sanitizer /tmp/logs

  header "Running test flavor $flavor"

  ./.ci/build.sh "$@"

  code=0
  meson test -C build --verbose || code=$?

  sudo tar -c -z -f "/tmp/logs/tests.$flavor.tar.gz" build/ sanitizer/

  return $code
}

case "$(uname -s)" in
MINGW* | Darwin) sudo() { "$@"; } ;;
esac

case "$1" in
default)
  run_tests default
  ;;
nolegacy)
  run_tests nolegacy -Dcrypto=nolegacy
  ;;
gcrypt)
  run_tests gcrypt -Dcrypto=gcrypt
  ;;
*)
  bail "unknown test flavor $1"
  ;;
esac

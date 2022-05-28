#!/bin/bash

# Fetch and build muon (a C reimplementation of the meson build system), and then use that to build tinc.

set -euo pipefail

prefix=/opt/tinc_muon

header() {
  echo >&2 '################################################################################'
  echo >&2 "# $*"
  echo >&2 '################################################################################'
}

header 'Fetch and build muon'

git clone https://git.sr.ht/~lattis/muon ~/muon
pushd ~/muon

./bootstrap.sh build
./build/muon setup build
ninja -C build
sudo ./build/muon -C build install

popd

header 'Setup build directory'
muon setup -D prefix=$prefix -D systemd=disabled build_muon
ninja -C build_muon

header 'Install tinc'
sudo muon -C build_muon install
$prefix/sbin/tinc --version
$prefix/sbin/tincd --version

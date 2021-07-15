#!/bin/sh
# A very simple harness to avoid creating a
# separate meson executable for each test.

wd="$PWD/test/wd"
mkdir -p "$wd"
cd "$wd" || exit 1

testcase=$1
echo >&2 "running testcase $testcase"

exec sh "$testcase"

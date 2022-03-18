#!/bin/sh

set -eu

. .ci/conf.sh

# shellcheck disable=SC2086
meson setup build $CONF_FLAGS "$@"

ninja -C build

set builddir=%1

meson test -C %builddir% --verbose --repeat 666 || exit 1

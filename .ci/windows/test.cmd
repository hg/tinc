set builddir=%1

meson test -C %builddir% --verbose || exit 1

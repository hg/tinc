set crypto=%1
set builddir=%crypto%
set args=

if %TYPE% == cross (
    set args=--cross-file .ci/cross/msvc/%ARCH:amd64_=%
)

echo configure build directory
meson setup %builddir% -Dbuildtype=release -Dcrypto=%crypto% %args% || exit 1

echo build project
meson compile -C %builddir% || exit 1

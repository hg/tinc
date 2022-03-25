set crypto=%1
set data=%crypto%\test-data

meson setup %crypto% -Dbuildtype=release -Dcrypto=%crypto% || exit 1
meson compile -C %crypto% || exit 1

mkdir %data% || exit 1

%crypto%\src\tinc --version || exit 1
%crypto%\src\tinc -c %data% -b init foo || exit 1
%crypto%\src\tinc -c %data% -b generate-ed25519-keys || exit 1

%crypto%\src\tincd --version || exit 1

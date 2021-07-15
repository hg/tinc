# Install build tools and dependencies

We assume that you already have the basic tools (git, compiler, linker, etc). Consult your favorite search engine if necessary.

meson 0.49+ and ninja are required. If the version in your repositories is too old, use pip.

**Note**: OpenSSL is required only if you leave the legacy protocol support enabled. Other libraries are optional and will be skipped if not available.

## Linux

### Alpine

    # apk add meson

### Arch Linux

    # pacman -S meson pkgconf openssl zlib lzo ncurses readline miniupnpc vde2 texinfo

### CentOS / AlmaLinux / RockyLinux

    # dnf config-manager --enable powertools
    # dnf install meson

### Debian / Ubuntu

    # apt install meson libssl-dev zlib1g-dev liblzo2-dev libncurses-dev libreadline-dev libminiupnpc-dev libvdeplug-dev texinfo

### Fedora

    # dnf install meson

## macOS

    $ brew install meson

## FreeBSD

    # export CFLAGS='-I/usr/local/include -L/usr/local/lib'
    # pkg install meson pkgconf openssl lzo2 ncurses miniupnpc readline texinfo

## OpenBSD

    # export CFLAGS='-I/usr/local/include -L/usr/local/lib'
    # pkg_add openssl-1.1.1k lzo2 miniupnpc readline texinfo

## NetBSD

    # export CFLAGS='-I/usr/pkg/include -L/usr/pkg/lib'
    # pkgin openssl lzo miniupnpc readline gtexinfo

## Windows

    $ pacman -S meson mingw-w64-x86_64-{python3,openssl,zlib,lzo2,ncurses,miniupnpc}

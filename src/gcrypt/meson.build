src_lib_crypto = files(
  'cipher.cc',
  'crypto.cc',
  'digest.cc',
  'pem.cc',
  'prf.cc',
  'rsa.cc',
  'rsagen.cc',
)

# Under current MinGW, flags specified in libgcrypt.pc fail on static build
if static and os_name == 'windows'
  dep_crypto = []
  foreach lib : ['libgcrypt', 'gpg-error']
    dep_crypto += cpp.find_library(lib, static: true)
  endforeach
else
  dep_crypto = dependency('libgcrypt', static: static)
endif

cdata.set('HAVE_LIBGCRYPT', 1)


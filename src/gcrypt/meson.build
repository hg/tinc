dep_gcrypt = dependency('libgcrypt')

tinc_dep += dep_gcrypt
tincd_dep += dep_gcrypt
sptps_test_dep += dep_gcrypt
sptps_speed_dep += dep_gcrypt
sptps_keypair_dep += dep_gcrypt

sptps_keypair_dep += dependency('openssl', required: false)

common = files(
  'cipher.c',
  'crypto.c',
  'digest.c',
  'prf.c',
)

tinc_src += [
  common,
  files(
    'pem.c',
    'rsa.c',
    'rsagen.c',
  )
]

tincd_src += [
  common,
  files(
    'pem.c',
    'rsa.c',
  )
]

sptps_test_src += common

sptps_speed_src += files(
  'crypto.c',
  'digest.c',
  'prf.c',
)

sptps_keypair_src += files('crypto.c')

cdata.set('HAVE_LIBGCRYPT', 1)


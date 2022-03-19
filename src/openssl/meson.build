dep_openssl = dependency('openssl11', required: false)
if not dep_openssl.found()
  dep_openssl = dependency('openssl')
endif

tinc_dep += dep_openssl
tincd_dep += dep_openssl
sptps_test_dep += dep_openssl
sptps_speed_dep += dep_openssl
sptps_keypair_dep += dep_openssl

common = files(
  'cipher.c',
  'crypto.c',
  'digest.c',
  'prf.c',
  'rsa.c',
)

tinc_src += [
  common,
  files('rsagen.c')
]

tincd_src += common

sptps_common = files(
  'crypto.c',
  'digest.c',
  'prf.c',
)

sptps_test_src += sptps_common
sptps_speed_src += sptps_common

sptps_keypair_src += files('crypto.c')

cdata.set('HAVE_OPENSSL', 1)


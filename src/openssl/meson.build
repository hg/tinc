dep_openssl = dependency('openssl')

foreach f : ['HMAC_CTX_new', 'BN_GENCB_new', 'RSA_set0_key']
  if cc.has_function(f, dependencies: dep_openssl)
    cdata.set('HAVE_' + f.to_upper(), 1)
  endif
endforeach

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

sptps_test_src += files(
  'crypto.c',
  'digest.c',
  'prf.c',
)

sptps_speed_src += files(
  'crypto.c',
  'digest.c',
  'prf.c',
)

sptps_keypair_src += files('crypto.c')

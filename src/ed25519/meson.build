src_ed25519 = files(
  'ecdh.cc',
  'ecdsa.cc',
  'ecdsagen.cc',
  'fe.cc',
  'ge.cc',
  'key_exchange.cc',
  'keypair.cc',
  'sc.cc',
  'sha512.cc',
  'sign.cc',
  'verify.cc',
)

lib_ed25519 = static_library(
  'ed25519',
  sources: src_ed25519,
  implicit_include_directories: false,
  include_directories: inc_conf,
  build_by_default: false,
)


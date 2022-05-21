src_chacha_poly = files(
  'chacha-poly1305.c',
  'chacha.c',
  'poly1305.c',
)

if cdata.has('HAVE_INDIRECT_FUNCTIONS') and cpu_family in ['x86', 'x86_64']
  src_chacha_poly += files('chacha_x86.c')
  cdata.set('HAVE_OPTIMIZED_CHACHA', 1)
endif

lib_chacha_poly = static_library(
  'chacha_poly',
  sources: src_chacha_poly,
  implicit_include_directories: false,
  include_directories: inc_conf,
  build_by_default: false,
)


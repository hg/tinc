foreach lib : ['ws2_32', 'gdi32', 'crypt32', 'iphlpapi']
  tinc_dep += cc.find_library(lib)
endforeach

ld_flags += '-static'

tincd_src += files('device.c')
tincd_cc_flags += '-DMINIUPNP_STATICLIB'

cdata.set('HAVE_MINGW', 1)


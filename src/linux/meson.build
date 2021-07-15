check_headers += 'linux/if_tun.h'

tincd_src += files('device.c')

if get_option('uml')
  cdata.set('ENABLE_UML', 1)
endif

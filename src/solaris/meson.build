dep_socket = cc.find_library('socket')
if not cc.has_function('connect', dependencies: dep_socket)
  error('required function connect missing')
endif

tincd_src += files('device.c')

cdata.set('HAVE_SOLARIS', 1)

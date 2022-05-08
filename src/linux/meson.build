check_headers += [
  'linux/if_tun.h',
  'linux/landlock.h',
  'netpacket/packet.h',
  'sys/epoll.h',
]

check_functions += 'recvmmsg'

src_tincd += files('device.c')

if opt_uml
  src_tincd += files('uml_device.c')
  cdata.set('ENABLE_UML', 1)
endif

dep_seccomp = dependency('libseccomp', required: opt_sandbox)
if dep_seccomp.found()
  src_tincd += files('tincd.c')
  deps_tincd += dep_seccomp
  src_tinc += files('../sandbox.c')
  cdata.set('HAVE_SANDBOX', 1)
endif

if cc.has_header('linux/landlock.h')
  src_tincd += files('landlock.c')
endif

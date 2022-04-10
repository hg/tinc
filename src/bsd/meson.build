check_headers += [
  'net/if_tap.h',
  'net/if_tun.h',
  'net/if_utun.h',
  'net/tap/if_tap.h',
  'net/tun/if_tun.h',
]

check_functions += [
  'devname',
  'fdevname',
]

src_tincd += files('device.cc')

if os_name == 'darwin'
  dep_tunemu = dependency('tunemu', required: opt_tunemu, static: static)
  dep_pcap = dependency('pcap', required: opt_tunemu, static: static)

  if dep_tunemu.found() and dep_pcap.found()
    deps_tincd += [dep_tunemu, dep_pcap]
    src_tincd += files('tunemu.cc')
    cdata.set('ENABLE_TUNEMU', 1)
  endif
endif


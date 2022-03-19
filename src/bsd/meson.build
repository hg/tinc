check_headers += [
  'net/if_tun.h',
  'net/if_utun.h',
  'net/if_tap.h',
  'net/tun/if_tun.h',
  'net/tap/if_tap.h',
]

tincd_src += files('device.c')

if os_name == 'darwin'
  opt_tunemu = get_option('tunemu')
  dep_tunemu = dependency('tunemu', required: opt_tunemu)
  dep_pcap = dependency('pcap', required: opt_tunemu)

  if dep_tunemu.found() and dep_pcap.found()
    tincd_dep += [dep_tunemu, dep_pcap]
    tincd_src += files('tunemu.c')
    cdata.set('ENABLE_TUNEMU', 1)
  endif
endif


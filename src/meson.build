conf_inc = include_directories('.')

cdata = configuration_data()

cdata.set_quoted('PACKAGE', meson.project_name())
cdata.set_quoted('VERSION', meson.project_version())
cdata.set_quoted('CONFDIR', sysconfdir)
cdata.set_quoted('RUNSTATEDIR', runstatedir)
cdata.set_quoted('LOCALSTATEDIR', localstatedir)
cdata.set_quoted('SBINDIR', sbindir)

cdata.set('HAVE_' + os_name.to_upper(), 1)

foreach attr : ['malloc', 'nonnull', 'warn_unused_result']
  cc.has_function_attribute(attr)
endforeach

check_headers = [
  'arpa/inet.h',
  'arpa/nameser.h',
  'dirent.h',
  'getopt.h',
  'inttypes.h',
  'net/ethernet.h',
  'net/if.h',
  'net/if_arp.h',
  'net/if_types.h',
  'netdb.h',
  'netinet/icmp6.h',
  'netinet/if_ether.h',
  'netinet/in.h',
  'netinet/in6.h',
  'netinet/in_systm.h',
  'netinet/ip.h',
  'netinet/ip6.h',
  'netinet/ip_icmp.h',
  'netinet/tcp.h',
  'netpacket/packet.h',
  'resolv.h',
  'stddef.h',
  'stdint.h',
  'strings.h',
  'sys/file.h',
  'sys/ioctl.h',
  'sys/mman.h',
  'sys/param.h',
  'sys/resource.h',
  'sys/socket.h',
  'sys/stat.h',
  'sys/time.h',
  'sys/types.h',
  'sys/un.h',
  'sys/wait.h',
  'syslog.h',
  'termios.h',
]

check_functions = [
  'asprintf',
  'daemon',
  'devname',
  'fchmod',
  'fdevname',
  'flock',
  'fork',
  'gettimeofday',
  'mlockall',
  'nanosleep',
  'putenv',
  'recvmmsg',
  'strsignal',
  'unsetenv',
  'vsyslog',
]

check_types = [
  'struct ether_header',
  'struct arphdr',
  'struct ether_arp',
  'struct ip',
  'struct icmp',
  'struct ip6_hdr',
  'struct icmp6_hdr',
  'struct nd_neighbor_solicit',
  'struct nd_opt_hdr',
]

# Same as project version, but with an additional commit hash.
git_tag = vcs_tag(
  command: './git_tag.sh',
  fallback: 'unknown',
  input: 'version_git.h.in',
  output: 'version_git.h',
)

subdir('ed25519')
subdir('chacha-poly1305')

common_src = [
  'conf.c',
  'dropin.c',
  'ed25519/ecdh.c',
  'ed25519/ecdsa.c',
  'keys.c',
  'list.c',
  'names.c',
  'netutl.c',
  'script.c',
  'splay_tree.c',
  'sptps.c',
  'subnet_parse.c',
  'utils.c',
  'version.c',
  'xoshiro.c',
  ed25519_src,
  chacha_poly_src,
  git_tag,
]

tinc_src = [
  'ed25519/ecdsagen.c',
  'fsck.c',
  'ifconfig.c',
  'info.c',
  'invitation.c',
  'tincctl.c',
  'top.c',
  common_src,
]

tincd_src = [
  'address_cache.c',
  'autoconnect.c',
  'buffer.c',
  'compression.h',
  'conf_net.c',
  'connection.c',
  'control.c',
  'dummy_device.c',
  'edge.c',
  'event.c',
  'fd_device.c',
  'graph.c',
  'logger.c',
  'meta.c',
  'multicast_device.c',
  'net.c',
  'net_packet.c',
  'net_setup.c',
  'net_socket.c',
  'node.c',
  'process.c',
  'protocol.c',
  'protocol_auth.c',
  'protocol_edge.c',
  'protocol_key.c',
  'protocol_misc.c',
  'protocol_subnet.c',
  'raw_socket_device.c',
  'route.c',
  'subnet.c',
  'tincd.c',
  common_src,
]

sptps_test_src = [
  'ed25519/ecdh.c',
  'ed25519/ecdsa.c',
  'logger.c',
  'sptps.c',
  'sptps_test.c',
  'utils.c',
  'xoshiro.c',
  chacha_poly_src,
  ed25519_src,
]

sptps_keypair_src = [
  'ed25519/ecdsagen.c',
  'sptps_keypair.c',
  'utils.c',
  ed25519_src,
]

sptps_speed_src = [
  'ed25519/ecdh.c',
  'ed25519/ecdsa.c',
  'ed25519/ecdsagen.c',
  'logger.c',
  'sptps.c',
  'sptps_speed.c',
  'utils.c',
  chacha_poly_src,
  ed25519_src,
]

ld_flags = []
tincd_cc_flags = []

tinc_dep = []
tincd_dep = [
  cc.find_library('m', required: false),
]
sptps_speed_dep = []
sptps_test_dep = []
sptps_keypair_dep = []

if os_name == 'linux'
  subdir('linux')
elif os_name.endswith('bsd') or os_name in ['dragonfly', 'darwin']
  subdir('bsd')
elif os_name == 'sunos'
  subdir('solaris')
elif os_name == 'windows'
  subdir('mingw')
endif

foreach h : check_headers
  if cc.has_header(h)
    cdata.set('HAVE_' + h.to_upper().underscorify(),
              1,
              description: '#include <' + h + '>')
  endif
endforeach

foreach f : check_functions
  if cc.has_function(f)
    cdata.set('HAVE_' + f.to_upper(),
              1,
              description: 'function ' + f)
  endif
endforeach

if cc.has_function('res_init', prefix: '''
  #include <netinet/in.h>
  #include <resolv.h>
''')
  cdata.set('HAVE_DECL_RES_INIT', 1)
endif

prefix_have = '''
#include "@0@/src/config.h"
#include "have.h"
'''.format(build_root)

type_conf = configuration_data()
type_conf.merge_from(cdata)
configure_file(output: 'config.h', configuration: type_conf)

foreach type : check_types
  if cc.has_type(type,
                 prefix: prefix_have,
                 args: cc_flags,
                 include_directories: conf_inc)
    name = 'HAVE_' + type.to_upper().underscorify()
    cdata.set(name, 1, description: type)
  endif
endforeach

dep_resolv = cc.find_library('resolv', required: false)

if not cdata.has('HAVE_GETOPT_H') or not cc.has_function('getopt_long')
  src = ['getopt.c', 'getopt1.c']
  tinc_src += src
  tincd_src += src
  sptps_test_src += src
  sptps_keypair_src += src
endif

dep_miniupnpc = dependency('miniupnpc', required: get_option('miniupnpc'))
if dep_miniupnpc.found()
  tincd_src += 'upnp.c'
  tincd_dep += [
    dependency('threads'),
    dep_miniupnpc,
  ]
  cdata.set('HAVE_MINIUPNPC', 1)
endif

# The meta-dependency covers more alternatives, but is only available in 0.54+
curses_name = meson.version().version_compare('>=0.54') ? 'curses' : 'ncurses'
dep_curses = dependency(curses_name, required: get_option('curses'))
if dep_curses.found()
  cdata.set('HAVE_CURSES', 1)
  tinc_dep += dep_curses
endif

# Some distributions do not supply pkg-config files for readline
opt_readline = get_option('readline')
if not opt_readline.disabled()
  dep_readline = dependency('readline', required: false)
  if not dep_readline.found()
    dep_readline = cc.find_library('readline', required: opt_readline)
  endif
  if dep_readline.found() and cc.has_header('readline/readline.h', dependencies: dep_readline) and cc.has_header('readline/history.h', dependencies: dep_readline)
    cdata.set('HAVE_READLINE', 1)
    tinc_dep += dep_readline
  endif
endif

dep_zlib = dependency('zlib', required: get_option('zlib'))
if dep_zlib.found()
  cdata.set('HAVE_ZLIB', 1)
  tincd_dep += dep_zlib
endif

opt_lzo = get_option('lzo')
if not opt_lzo.disabled()
  dep_lzo = dependency('lzo2', required: false)
  if not dep_lzo.found()
    dep_lzo = cc.find_library('lzo2', required: opt_lzo)
  endif
  if dep_lzo.found() and cc.has_function('lzo1x_1_compress', dependencies: dep_lzo) and cc.has_header('lzo1x.h', dependencies: dep_lzo)
    cdata.set('HAVE_LZO', 1)
    tincd_dep += dep_lzo
  endif
endif

opt_lz4 = get_option('lz4')
if not opt_lz4.disabled()
  dep_lz4 = dependency('liblz4', required: false)
  if dep_lz4.found()
    tincd_dep += dep_lz4
    cdata.set('HAVE_LZ4', 1)
    cdata.set('LZ4_H', '<lz4.h>')
  elif not opt_lz4.auto()
    tincd_src += 'lib/lz4/lz4.c'
    cdata.set('HAVE_LZ4', 1)
    cdata.set('LZ4_H', '"lib/lz4/lz4.h"')
  endif
endif

opt_vde = get_option('vde')
if not opt_vde.disabled()
  dep_vde = dependency('vdeplug', required: opt_vde)
  dep_dl = cc.find_library('dl', required: opt_vde)
  if dep_vde.found() and dep_dl.found()
    cdata.set('ENABLE_VDE', 1)
    tincd_src += 'vde_device.c'
    tincd_dep += [dep_dl, dep_vde]
  endif
endif

opt_crypto = get_option('crypto')
if opt_crypto == 'nolegacy'
  subdir('nolegacy')
else
  if opt_crypto == 'openssl'
    subdir('openssl')
  elif opt_crypto == 'gcrypt'
    subdir('gcrypt')
  else
    error('unknown crypto option ' + opt_crypto)
  endif
  digest = 'digest.c'
  tinc_src += digest
  tincd_src += [digest, 'cipher.c']
  sptps_test_src += digest
  sptps_speed_src += digest
endif

if get_option('jumbograms')
  cdata.set('ENABLE_JUMBOGRAMS', 1)
endif

if get_option('uml')
  tincd_src += 'uml_device.c'
endif

configure_file(output: 'config.h',
               configuration: cdata)

tinc_exe = executable(
  'tinc',
  sources: tinc_src,
  dependencies: tinc_dep,
  include_directories: conf_inc,
  link_args: ld_flags,
  install: true,
  install_dir: sbindir,
)

tincd_exe = executable(
  'tincd',
  sources: tincd_src,
  dependencies: tincd_dep,
  include_directories: conf_inc,
  c_args: tincd_cc_flags,
  link_args: ld_flags,
  install: true,
  install_dir: sbindir,
)

sptps_test_ld_flags = ld_flags

if os_name == 'windows'
  sptps_test_ld_flags += '-pthread'
endif

sptps_test_exe = executable(
  'sptps_test',
  sources: sptps_test_src,
  dependencies: sptps_test_dep,
  include_directories: conf_inc,
  link_args: sptps_test_ld_flags,
  build_by_default: false,
)

sptps_keypair_exe = executable(
  'sptps_keypair',
  sources: sptps_keypair_src,
  dependencies: sptps_keypair_dep,
  include_directories: conf_inc,
  link_args: ld_flags,
  build_by_default: false,
)

if os_name == 'linux'
  sptps_speed_dep += cc.find_library('rt')

  sptps_speed_exe = executable(
    'sptps_speed',
    sources: sptps_speed_src,
    dependencies: sptps_speed_dep,
    include_directories: conf_inc,
    link_args: ld_flags,
    build_by_default: false,
  )
endif


project('tinc', 'c',
  version: run_command('./src/git_tag.sh', '--abbrev=0').stdout().strip(),
  meson_version: '>=0.49',
  default_options: [
    'c_std=c99',
    'warning_level=3',
  ],
)

cc = meson.get_compiler('c')
os_name = host_machine.system()

cc_flags = ['-D_GNU_SOURCE']
add_project_arguments(cc_flags, language: 'c')

build_root = meson.build_root()
src_root = meson.source_root()

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
mandir = prefix / get_option('mandir')
libdir = prefix / get_option('libdir')
datadir = prefix / get_option('datadir')
infodir = prefix / get_option('infodir')
sbindir = prefix / get_option('sbindir')
localedir = prefix / get_option('localedir')
sysconfdir = prefix / get_option('sysconfdir')
localstatedir = prefix / get_option('localstatedir')

runstatedir = get_option('runstatedir')
if runstatedir == ''
  runstatedir = localstatedir / 'run'
endif

subdir('doc')
subdir('src')
subdir('test')
subdir('bash_completion.d')

if os_name == 'linux' and not get_option('systemd').disabled()
  subdir('systemd')
endif

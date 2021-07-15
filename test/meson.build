tests = [
  'basic.test',
  'commandline.test',
  'executables.test',
  'import-export.test',
  'invite-join.test',
  'invite-offline.test',
  'invite-tinc-up.test',
  'scripts.test',
  'security.test',
  'variables.test',
]

if get_option('legacy')
  if os_name != 'windows'
    tests += 'algorithms.test'
  endif
  tests += 'legacy-protocol.test'
endif

if os_name != 'windows'
  tests += 'sptps-basic.test'
endif

if os_name == 'linux'
  tests += 'ns-ping.test'
endif

splice_exe = executable(
  'splice',
  sources: ['splice.c'],
  include_directories: conf_inc,
)

harness = find_program('./harness.sh')

env = environment()
env.set('tincd_path', tincd_exe.full_path())
env.set('tinc_path', tinc_exe.full_path())
env.set('SPTPS_TEST', sptps_test_exe.full_path())
env.set('SPTPS_KEYPAIR', sptps_keypair_exe.full_path())
env.set('SPLICE_PATH', splice_exe.full_path())
env.set('TESTLIB_PATH', src_root / 'test' / 'testlib.sh')

foreach test_name : tests
  test_path = meson.current_source_dir() / test_name

  test(test_name,
       harness,
       timeout: 600,
       env: env,
       args: [test_path])
endforeach

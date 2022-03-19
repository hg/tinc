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

if get_option('crypto') != 'nolegacy'
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
  build_by_default: false,
)

env = environment()
env.set('TINC_PATH', tinc_exe.full_path())
env.set('TINCD_PATH', tincd_exe.full_path())
env.set('SPTPS_TEST_PATH', sptps_test_exe.full_path())
env.set('SPTPS_KEYPAIR_PATH', sptps_keypair_exe.full_path())
env.set('SPLICE_PATH', splice_exe.full_path())
env.set('TESTLIB_PATH', src_root / 'test' / 'testlib.sh')

test_dep = [
  tinc_exe,
  tincd_exe,
  splice_exe,
  sptps_test_exe,
  sptps_keypair_exe,
]

foreach test_name : tests
  target = find_program(test_name, native: true)
  test(test_name, target, timeout: 180, env: env, depends: test_dep)
endforeach


systemd = dependency('systemd', required: get_option('systemd'))
if not systemd.found()
  subdir_done()
endif

systemd_dir = get_option('systemd-dir')
if systemd_dir == ''
  systemd_dir = systemd.get_pkgconfig_variable('systemdsystemunitdir', define_variable: ['prefix', prefix])
endif

systemd_conf = configuration_data()
systemd_conf.set('sysconfdir', sysconfdir)
systemd_conf.set('sbindir', sbindir)

configure_file(input: 'tinc.service.in',
               output: 'tinc.service',
               configuration: systemd_conf,
               install_dir: systemd_dir)

configure_file(input: 'tinc@.service.in',
               output: 'tinc@.service',
               configuration: systemd_conf,
               install_dir: systemd_dir)

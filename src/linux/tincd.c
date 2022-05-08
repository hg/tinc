#include "../system.h"

#include <assert.h>
#include <sys/prctl.h>
#include <sys/shm.h>
#include <libgen.h>

#include "sandbox.h"
#include "../names.h"
#include "../sandbox.h"
#include "../logger.h"

#ifdef HAVE_LINUX_LANDLOCK_H
#include "landlock.h"
#endif

static sandbox_level_t current_level = SANDBOX_NORMAL;
static bool entered = false;

static void print_blocking(const char *type) {
	logger(DEBUG_ALWAYS, LOG_DEBUG, "Blocking syscalls: %s", type);
}

// Block syscalls that require superuser privileges, or any capabilities.
static bool block_syscalls_privileged(scmp_filter_ctx ctx) {
	print_blocking("privileged");

	// memory locking
	DENY_CALL(mlock);
	DENY_CALL(mlock2);
	DENY_CALL(mlockall);
	DENY_CALL(munlock);
	DENY_CALL(munlockall);

	// changing file ownership
	DENY_CALL(chown);
	DENY_CALL(chown32);
	DENY_CALL(fchown);
	DENY_CALL(fchown32);
	DENY_CALL(fchownat);
	DENY_CALL(lchown);
	DENY_CALL(lchown32);

	// various privileged
	DENY_CALL(acct);
	DENY_CALL(bpf);
	DENY_CALL(capset);
	DENY_CALL(fanotify_init);
	DENY_CALL(fanotify_mark);
	DENY_CALL(nfsservctl);
	DENY_CALL(open_by_handle_at);
	DENY_CALL(quotactl);
	DENY_CALL(setdomainname);
	DENY_CALL(sethostname);
	DENY_CALL(vhangup);
	DENY_CALL(reboot);

	// kernel keyring
	DENY_CALL(add_key);
	DENY_CALL(keyctl);
	DENY_CALL(request_key);

	// namespaces
	DENY_CALL(setns);
	DENY_CALL(unshare);

	// FS mounting
	DENY_CALL(chroot);
	DENY_CALL(mount);
	DENY_CALL(pivot_root);
	DENY_CALL(umount);
	DENY_CALL(umount2);
#ifdef __NR_move_mount
	DENY_CALL(move_mount);
#endif
#ifdef __NR_open_tree
	DENY_CALL(open_tree);
#endif
#if defined(__NR_mount_setattr) && defined(__SNR_mount_setattr)
	DENY_CALL(mount_setattr);
#endif
#ifdef __NR_fsconfig
	DENY_CALL(fsconfig);
#endif
#ifdef __NR_fsmount
	DENY_CALL(fsmount);
#endif
#ifdef __NR_fsopen
	DENY_CALL(fsopen);
#endif
#ifdef __NR_fspick
	DENY_CALL(fspick);
#endif

	// changing time
	DENY_CALL(adjtimex);
	DENY_CALL(clock_adjtime);
	DENY_CALL(clock_settime);
#ifdef __NR_clock_adjtime64
	DENY_CALL(clock_adjtime64);
#endif
#ifdef __NR_clock_settime64
	DENY_CALL(clock_settime64);
#endif
	DENY_CALL(settimeofday);

	// kernel modules
	DENY_CALL(create_module);
	DENY_CALL(delete_module);
	DENY_CALL(finit_module);
	DENY_CALL(init_module);

	// raw I/O
	DENY_CALL(ioperm);
	DENY_CALL(iopl);
	DENY_CALL(pciconfig_iobase);
	DENY_CALL(pciconfig_read);
	DENY_CALL(pciconfig_write);

	// debug
	DENY_CALL(kcmp);
	DENY_CALL(lookup_dcookie);
	DENY_CALL(perf_event_open);
#ifndef HAVE_SANITIZER_ADDRESS
	DENY_CALL(ptrace);
#endif
	DENY_CALL(rtas);
	DENY_CALL(sys_debug_setcontext);
	DENY_CALL(syslog);
#if defined(__NR_pidfd_getfd) && defined(__SNR_pidfd_getfd)
	DENY_CALL(pidfd_getfd);
#endif

	// set user/group ID
	DENY_CALL(setgroups);
	DENY_CALL(setgroups32);

	return true;
}

// Since seccomp filters are inherited by child processes, we have to be *very*
// conservative here, or tincd scripts may fail (those can do anything at all:
// load kernel modules, reboot the system, whatever).
static bool block_syscalls_safe(scmp_filter_ctx ctx) {
	print_blocking("'safe' list");

	// obsolete and unimplemented
	DENY_CALL(_sysctl);
	DENY_CALL(afs_syscall);
	DENY_CALL(bdflush);
	DENY_CALL(create_module);
	DENY_CALL(ftime);
	DENY_CALL(get_kernel_syms);
	DENY_CALL(getpmsg);
	DENY_CALL(gtty);
	DENY_CALL(idle);
	DENY_CALL(lock);
	DENY_CALL(mpx);
	DENY_CALL(prof);
	DENY_CALL(profil);
	DENY_CALL(putpmsg);
	DENY_CALL(query_module);
	DENY_CALL(security);
	DENY_CALL(sgetmask);
	DENY_CALL(ssetmask);
	DENY_CALL(stime);
	DENY_CALL(stty);
	DENY_CALL(sysfs);
	DENY_CALL(tuxcall);
	DENY_CALL(ulimit);
	DENY_CALL(uselib);
	DENY_CALL(ustat);
	DENY_CALL(vserver);

	// Strictly speaking, some calls below may be needed by tincd scripts, but I very much
	// doubt somebody is using them to control swap or load new kernel.

	// swap
	DENY_CALL(swapoff);
	DENY_CALL(swapon);

	// kexec
	DENY_CALL(kexec_file_load);
	DENY_CALL(kexec_load);

	return true;
}

#define DENY_MMAP(call, flags) \
	if(seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(call), 1, SCMP_A2(SCMP_CMP_MASKED_EQ, (flags), (flags))) < 0) return false

// Block attempts to create memory regions (or change existing ones)
// that are both writable and executable.
static bool block_writable_code(scmp_filter_ctx ctx) {
	print_blocking("making writable memory executable");

	DENY_MMAP(mprotect, PROT_EXEC);
	DENY_MMAP(pkey_mprotect, PROT_EXEC);
	DENY_MMAP(shmat, SHM_EXEC);
	DENY_MMAP(mmap, PROT_EXEC | PROT_WRITE);
	DENY_MMAP(mmap2, PROT_EXEC | PROT_WRITE);

	return true;
}

// Prevent tincd from spawning child processes.
static bool block_syscalls_exec(scmp_filter_ctx ctx) {
	print_blocking("process creation");

	// process creation
#ifndef HAVE_SANITIZER_ADDRESS
	DENY_CALL(clone);
#endif
	DENY_CALL(execve);
	DENY_CALL(fork);
	DENY_CALL(vfork);
#ifdef __NR_execveat
	DENY_CALL(execveat);
#endif
#ifdef __NR_clone3
	DENY_CALL(clone3);
#endif

	return true;
}

// Remove access to anything potentially dangerous that's not used by tincd or its libraries.
static bool block_syscalls_unused(scmp_filter_ctx ctx) {
	print_blocking("unused by tincd");

	// files
	DENY_CALL(chdir);
	DENY_CALL(flock);
	DENY_CALL(fsetxattr);
	DENY_CALL(ftruncate);
	DENY_CALL(lsetxattr);
	DENY_CALL(mknod);
	DENY_CALL(setxattr);
	DENY_CALL(truncate);
	DENY_CALL(utime);

	// set user/group ID
	DENY_CALL(setgid);
	DENY_CALL(setgid32);
	DENY_CALL(setregid);
	DENY_CALL(setregid32);
	DENY_CALL(setresgid);
	DENY_CALL(setresgid32);
	DENY_CALL(setresuid);
	DENY_CALL(setresuid32);
	DENY_CALL(setreuid);
	DENY_CALL(setreuid32);
	DENY_CALL(setuid);
	DENY_CALL(setuid32);

	// shared memory
	DENY_CALL(shmat);
	DENY_CALL(shmctl);
	DENY_CALL(shmdt);
	DENY_CALL(shmget);

	// memory protection keys
	DENY_CALL(pkey_alloc);
	DENY_CALL(pkey_free);
	DENY_CALL(pkey_mprotect);

	// async I/O
	DENY_CALL(io_cancel);
	DENY_CALL(io_destroy);
	DENY_CALL(io_getevents);
	DENY_CALL(io_setup);
	DENY_CALL(io_submit);
#ifdef __NR_io_pgetevents
	DENY_CALL(io_pgetevents);
#endif
#ifdef __NR_io_pgetevents_time64
	DENY_CALL(io_pgetevents_time64);
#endif
#ifdef __NR_io_uring_enter
	DENY_CALL(io_uring_enter);
	DENY_CALL(io_uring_register);
	DENY_CALL(io_uring_setup);
#endif

	// ipc
	DENY_CALL(ipc);
	DENY_CALL(memfd_create);
	DENY_CALL(mq_getsetattr);
	DENY_CALL(mq_notify);
	DENY_CALL(mq_open);
	DENY_CALL(mq_timedreceive);
	DENY_CALL(mq_timedsend);
	DENY_CALL(mq_unlink);
	DENY_CALL(msgctl);
	DENY_CALL(msgget);
	DENY_CALL(msgrcv);
	DENY_CALL(msgsnd);
	DENY_CALL(process_vm_readv);
	DENY_CALL(process_vm_writev);
	DENY_CALL(semctl);
	DENY_CALL(semget);
	DENY_CALL(semop);
	DENY_CALL(semtimedop);
#ifdef __NR_mq_timedreceive_time64
	DENY_CALL(mq_timedreceive_time64);
#endif
#ifdef __NR_mq_timedsend_time64
	DENY_CALL(mq_timedsend_time64);
#endif
#if defined(__NR_process_madvise) && defined(__SNR_process_madvise)
	DENY_CALL(process_madvise);
#endif
#ifdef __NR_semtimedop_time64
	DENY_CALL(semtimedop_time64);
#endif

	// sending signals
	DENY_CALL(kill);
	DENY_CALL(rt_sigqueueinfo);
	DENY_CALL(rt_tgsigqueueinfo);
	DENY_CALL(tgkill);
	DENY_CALL(tkill);
#ifdef __NR_pidfd_send_signal
	DENY_CALL(pidfd_send_signal);
#endif

	// resources
	DENY_CALL(setpriority);
	DENY_CALL(setrlimit);
	DENY_CALL(ioprio_set);
	DENY_CALL(nice);
	DENY_CALL(sched_setaffinity);
	DENY_CALL(sched_setattr);
	DENY_CALL(sched_setparam);
	DENY_CALL(sched_setscheduler);

	// NUMA
	DENY_CALL(mbind);
	DENY_CALL(migrate_pages);
	DENY_CALL(move_pages);
	DENY_CALL(set_mempolicy);

	// landlock
#if defined(__NR_landlock_add_rule) && defined(__SNR_landlock_add_rule)
	DENY_CALL(landlock_create_ruleset);
	DENY_CALL(landlock_add_rule);
	DENY_CALL(landlock_restrict_self);
#endif

	// misc
	DENY_CALL(seccomp);
	DENY_CALL(personality);

	// CPU emulation
	DENY_CALL(modify_ldt);
	DENY_CALL(subpage_prot);
	DENY_CALL(switch_endian);
	DENY_CALL(vm86);
	DENY_CALL(vm86old);

	// timers
	DENY_CALL(alarm);
	DENY_CALL(getitimer);
	DENY_CALL(setitimer);
	DENY_CALL(timer_create);
	DENY_CALL(timer_delete);
	DENY_CALL(timer_getoverrun);
	DENY_CALL(timer_gettime);
	DENY_CALL(timer_gettime64);
	DENY_CALL(timer_settime);
	DENY_CALL(timer_settime64);
	DENY_CALL(timerfd_create);
	DENY_CALL(timerfd_gettime);
	DENY_CALL(timerfd_gettime64);
	DENY_CALL(timerfd_settime);
	DENY_CALL(timerfd_settime64);
	DENY_CALL(times);

	return true;
}

// true if the current process is running under root, or has any capabilities.
static bool is_privileged(void) {
	if(getuid() == 0) {
		return true;
	}

	// Now check capabilities and make sure there aren't any. Doing that through a
	// convenient API requires linking to yet another library, and our needs are
	// very simple, so extract that information from /proc.

	char buf[512];
	snprintf(buf, sizeof(buf), "/proc/%d/status", getpid());

	FILE *f = fopen(buf, "r");

	if(!f) {
		return true;
	}

	while(fgets(buf, sizeof(buf), f)) {
		const char *name = strtok(buf, "\t");

		if(!strcmp(name, "CapPrm:") || !strcmp(name, "CapEff:") || !strcmp(name, "CapAmb:")) {
			const char *flags = strtok(NULL, "\t\n");

			// Check that all flags are zero. If not, at least one capability is used.
			if(flags && strspn(flags, "0") < strlen(flags)) {
				logger(DEBUG_ALWAYS, LOG_DEBUG, "tincd has capabilities, leaving privileged syscalls");
				fclose(f);
				return true;
			}
		}
	}

	fclose(f);
	return false;
}

static bool setup_syscall_denylist(scmp_filter_ctx ctx, bool privileged, bool can_exec) {
	if(!block_syscalls_safe(ctx)) {
		return false;
	}

	if(!block_writable_code(ctx)) {
		return false;
	}

	// If tincd is running under an ordinary user, we'll not be able to use privileged
	// syscalls even through scripts (since SUID binaries are disabled by NO_NEW_PRIVS).
	// If it's running under root, but scripts are disabled, these syscalls are also not
	// expected to be called — there will be no script processes, and tincd initialization
	// have finished by the time we're entering sandbox.
	if((!privileged || !can_exec) && !block_syscalls_privileged(ctx)) {
		return false;
	}

	if(can_exec) {
		return true;
	} else {
		return block_syscalls_exec(ctx) &&
		       block_syscalls_unused(ctx);
	}
}

static bool setup_seccomp_bpf(bool privileged, bool can_exec) {
	scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);

	if(!ctx) {
		return false;
	}

	bool success = setup_syscall_denylist(ctx, privileged, can_exec) &&
	               !seccomp_load(ctx);

	seccomp_release(ctx);
	return success;
}

static bool sandbox_can_after_enter(sandbox_action_t action) {
	switch(action) {
	case START_PROCESSES:
	case USE_NEW_PATHS:
		return current_level < SANDBOX_HIGH;

	default:
		abort();
	}
}

bool sandbox_can(sandbox_action_t action, sandbox_time_t when) {
	if(when == AFTER_SANDBOX || entered) {
		return sandbox_can_after_enter(action);
	} else {
		return true;
	}
}

void sandbox_set_level(sandbox_level_t level) {
	current_level = level;
}

static bool prctl_drop_privs(void) {
	return prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != -1 &&
	       prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != -1;
}

#ifdef HAVE_LINUX_LANDLOCK_H
static void conf_subdir(char *buf, const char *name) {
	snprintf(buf, PATH_MAX, "%s/%s", confbase, name);
}

static bool add_path_rules(void) {
	char cache[PATH_MAX], hosts[PATH_MAX], invitations[PATH_MAX];
	conf_subdir(cache, "cache");
	conf_subdir(hosts, "hosts");
	conf_subdir(invitations, "invitations");

	char *logdir = NULL;

	if(logfilename) {
		char *logf = alloca(strlen(logfilename) + 1);
		strcpy(logf, logfilename);
		logdir = dirname(logf);
	}

	char *pidf = alloca(strlen(pidfilename) + 1);
	strcpy(pidf, pidfilename);

	char *unixf = alloca(strlen(unixsocketname) + 1);
	strcpy(unixf, unixsocketname);

	const landlock_path_t paths[] = {
		{"/dev/random",  FS_READ_FILE},
		{"/dev/urandom", FS_READ_FILE},
		{logdir,         FS_MAKE_REG},
		{logfilename,    FS_WRITE_FILE},
		{dirname(pidf),  FS_REMOVE_FILE},
		{dirname(unixf), FS_REMOVE_FILE},
		{confbase,       FS_READ_FILE | FS_READ_DIR},
		{cache,          FS_READ_FILE | FS_WRITE_FILE | FS_MAKE_REG | FS_REMOVE_FILE | FS_READ_DIR},
		{hosts,          FS_READ_FILE | FS_WRITE_FILE | FS_MAKE_REG | FS_REMOVE_FILE | FS_READ_DIR},
		{invitations,    FS_READ_FILE | FS_WRITE_FILE | FS_MAKE_REG | FS_REMOVE_FILE | FS_READ_DIR},
		{NULL,           0}
	};
	return allow_paths(paths);
}
#endif // HAVE_LINUX_LANDLOCK_H

bool sandbox_enter(void) {
	assert(!entered);
	entered = true;

	if(current_level == SANDBOX_NONE) {
		logger(DEBUG_ALWAYS, LOG_DEBUG, "Sandbox is disabled");
		return true;
	}

	if(!prctl_drop_privs()) {
		logger(DEBUG_ALWAYS, LOG_ERR, "Failed to disable privilege escalation: %s", strerror(errno));
		return false;
	}

	bool privileged = is_privileged();
	bool can_exec = sandbox_can_after_enter(START_PROCESSES);

#ifdef HAVE_LINUX_LANDLOCK_H

	if(!sandbox_can_after_enter(USE_NEW_PATHS) && !add_path_rules()) {
		logger(DEBUG_ALWAYS, LOG_ERR, "Failed to block filesystem access: %s", strerror(errno));
		return false;
	}

#endif

	if(!setup_seccomp_bpf(privileged, can_exec)) {
		logger(DEBUG_ALWAYS, LOG_ERR, "Error setting up seccomp sandbox: %s", strerror(errno));
		return false;
	}

	logger(DEBUG_ALWAYS, LOG_DEBUG, "Entered sandbox at level %d", current_level);
	return true;
}

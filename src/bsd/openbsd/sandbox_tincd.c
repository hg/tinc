#include "../../system.h"

#include <libgen.h>
#include <assert.h>

#include "sandbox.h"
#include "../../device.h"
#include "../../logger.h"
#include "../../names.h"
#include "../../net.h"
#include "../../sandbox.h"
#include "../../script.h"
#include "../../xalloc.h"
#include "../../proxy.h"

static const unveil_path_t base_paths[] = {
	{"/dev/random",         "r"},
	{"/dev/urandom",        "r"},
	{"/usr/lib",            "r"},
	{"/usr/local/lib",      "r"},
	{"/usr/local/share",    "r"},
	{"/usr/share/locale",   "r"},
	{"/usr/share/zoneinfo", "r"},
	{NULL,                  NULL},
};

static const unveil_path_t bin_paths[] = {
	{"/bin",                "rx"},
	{"/sbin",               "rx"},
	{"/usr/bin",            "rx"},
	{"/usr/sbin",           "rx"},
	{"/usr/local/bin",      "rx"},
	{"/usr/local/sbin",     "rx"},
	{NULL,                  NULL},
};

static void paths_common(void) {
	allow_paths(base_paths);

	// Dummy device uses a fake path, skip it
	const char *dev = strcmp(device, "dummy") ? device : NULL;

	const unveil_path_t runtime_paths[] = {
#ifdef ENABLE_VDE
		{RUNSTATEDIR,    "rwc"},
#endif
		{LOCALSTATEDIR,  "rwc"},
		{confbase,       enable_scripts ? "rwcx" : "rwc"},
		{dev,            "rw"},
		{logfilename,    "rwc"},
		{pidfilename,    "rwc"},
		{unixsocketname, "rwc"},
		{NULL,           NULL},
	};
	allow_paths(runtime_paths);
}

static void paths_exec(void) {
	const char *interpreter = scriptinterpreter && *scriptinterpreter
	                          ? scriptinterpreter
	                          : NULL;

	char *exe = exec_proxy_path();

	const unveil_path_t paths[] = {
		{interpreter, "rx"},
		{exe,         "rx"},
		{NULL,        NULL},
	};
	allow_paths(paths);
	free(exe);

	if(!interpreter) {
		allow_paths(bin_paths);
	}
}

static bool pledge_privileges(bool need_exec) {
	// no mcast since multicasting should be set up by now
	char promises[512] =
	        "stdio"  // General I/O, both disk and network
	        " rpath" // Read files and directories
	        " wpath" // Write files and directories
	        " cpath" // Create new ones
	        " dns"   // Resolve domain names
	        " inet"  // Make network connections
	        " unix"; // Control socket connections from tinc CLI

	const char *execpromises;

	if(need_exec) {
		// fork() and execve() for scripts and exec proxies
		const char *exec = " proc exec";
		size_t n = strlcat(promises, exec, sizeof(promises));
		assert(n < sizeof(promises));
		execpromises = NULL; // run children with full privileges
	} else {
		execpromises = ""; // deny everything to children we couldn't spawn anyway
	}

	return restrict_privs(promises, execpromises);
}

bool sandbox_tincd(void) {
	const bool need_exec = enable_scripts || proxytype == PROXY_EXEC;

	// Restrict paths unless running in a chroot
	if(confbase && *confbase) {
		paths_common();

		if(need_exec) {
			paths_exec();
		}
	}

	return pledge_privileges(need_exec);
}


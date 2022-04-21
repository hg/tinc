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

// Sadly, we cannot use execpromises to put restrictions on tincd scripts since
// users expect them to run unrestricted and be able to do anything the user can
// do. This limits the effectiveness of the sandbox since an attacker can spawn
// a shell and then do whatever he wants. Still, it's better than nothing.
bool sandbox_tincd(void) {
	const unveil_path_t paths[] = {
		{"/dev/random",    "r"},
		{"/dev/urandom",   "r"},
		{"/usr/lib",       "r"},
		{"/usr/local/lib", "r"},
		{RUNSTATEDIR,      "rw"},
		{LOCALSTATEDIR,    "rw"},
		{device,           "rw"},
		{logfilename,      "rwc"},
		{pidfilename,      "rwc"},
		{unixsocketname,   "rwc"},
		{confbase,         enable_scripts ? "rwxc" : "rwc"},
		{NULL,             NULL},
	};
	allow_paths(paths);

	const bool need_exec = enable_scripts || proxytype == PROXY_EXEC;

	if(need_exec) {
		const char *interp = scriptinterpreter && *scriptinterpreter
		                     ? scriptinterpreter
		                     : NULL;

		const unveil_path_t bin_paths[] = {
			{"/bin",           "rx"},
			{"/sbin",          "rx"},
			{"/usr/bin",       "rx"},
			{"/usr/local/bin", "rx"},
			{interp,           "rx"},
			{proxy_exe(),      "rx"},
			{NULL,             NULL},
		};
		allow_paths(bin_paths);
	}

	// no mcast since multicast should be set up by now
	char promises[512] =
	        "stdio"  // General I/O, both disk and network
	        " rpath" // Read files and directories
	        " wpath" // Write files and directories
	        " cpath" // Create new ones
	        " dns"   // Resolve domain names
	        " inet"  // Make network connections
	        " unix"; // Control socket connections from tinc CLI

	if(need_exec) {
		// fork() and execve() for scripts and exec proxies
		const char *exec = " proc exec";
		size_t n = strlcpy(promises, exec, sizeof(promises));
		assert(n < sizeof(promises));
	}

	fprintf(stderr, "running pledge '%s'\n", promises);
	return restrict_privs(promises);
}


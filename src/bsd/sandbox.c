#include "../system.h"

#include <libgen.h>

#include "../device.h"
#include "../logger.h"
#include "../names.h"
#include "../sandbox.h"
#include "../xalloc.h"
#include "../script.h"

typedef struct unveil_path_t {
	const char *path;
	const char *priv;
} unveil_path_t;

static void allow_paths(const unveil_path_t paths[]) {
	// Since some path variables may contain NULL, we check priv here.
	// If a NULL path is seen, just skip it.
	for(const unveil_path_t *p = paths; p->priv; ++p) {
		if(p->path && unveil(p->path, p->priv)) {
			logger(DEBUG_ALWAYS, LOG_ERR, "unveil(%s, %s) failed: %s", p->path, p->priv, strerror(errno));
		}
	}
}

static bool restrict_privs(const char *promises) {
	if(pledge(promises, NULL)) {
		logger(DEBUG_ALWAYS, LOG_ERR, "pledge sandbox failed: %s", strerror(errno));
		return false;
	} else {
		return true;
	}
}

bool sandbox_tinc(void) {
	const char *promises =
	        "stdio"  // General I/O
	        " rpath" // Read configs & keys
	        " wpath" // Write same
	        " cpath" // Create same
	        " fattr" // chmod() same
	        " proc"  // Check that tincd is running with kill()
	        " dns"   // Resolve domain names
	        " inet"  // Check that port is available
	        " unix"  // Control connection to tincd
	        " exec"  // Start tincd
#if defined(HAVE_CURSES) || defined(HAVE_READLINE)
	        " tty"
#endif
	        ;
	return restrict_privs(promises);
}

static char *proxy_exe(void) {
	if(proxytype == PROXY_EXEC && proxyhost) {
		char *cmd = xstrdup(proxyhost);
		char *tok = strtok(cmd, " \t\n");
		char *result = tok ? xstrdup(tok) : NULL;
		free(cmd);
		return result;
	} else {
		return NULL;
	}
}

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

	if(enable_scripts || proxytype == PROXY_EXEC) {
		const unveil_path_t bin_paths[] = {
			{"/bin",            "rx"},
			{"/sbin",           "rx"},
			{"/usr/bin",        "rx"},
			{"/usr/local/bin",  "rx"},
			{scriptinterpreter, "rx"},
			{proxy_cmd(),       "rx"},
			{NULL,              NULL},
		};
		allow_paths(bin_paths);
	}

	// no mcast since multicast should be set up by now
	const char *promises =
	        "stdio"  // General I/O, both disk and network
	        " rpath" // Read files and directories
	        " wpath" // Write files and directories
	        " cpath" // Create new ones
	        " dns"   // Resolve domain names
	        " inet"  // Make network connections
	        " unix"  // Control socket connections from tinc CLI
	        " proc"  // fork() for scripts and exec proxies
	        " exec"  // execve(), same
	        ;
	return restrict_privs(promises);
}


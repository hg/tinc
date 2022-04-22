#include "../../system.h"

#include "sandbox.h"
#include "../../sandbox.h"

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

bool sandbox_tinc(void) {
	return restrict_privs(promises, NULL);
}


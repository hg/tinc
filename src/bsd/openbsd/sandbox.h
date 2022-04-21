#ifndef TINC_BSD_OPENBSD_SANDBOX_H
#define TINC_BSD_OPENBSD_SANDBOX_H

#include "../../system.h"

typedef struct unveil_path_t {
	const char *path;
	const char *priv;
} unveil_path_t;

extern void allow_paths(const unveil_path_t paths[]);
extern bool restrict_privs(const char *promises);

#endif // TINC_BSD_OPENBSD_SANDBOX_H


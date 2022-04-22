#include "../../system.h"

#include "sandbox.h"
#include "../../logger.h"

void allow_paths(const unveil_path_t paths[]) {
	// Since some path variables may contain NULL, we check priv here.
	// If a NULL path is seen, just skip it.
	for(const unveil_path_t *p = paths; p->priv; ++p) {
		if(p->path) {
			logger(DEBUG_ALWAYS, LOG_DEBUG, "Unveiling path %s with %s", p->path, p->priv);

			if(unveil(p->path, p->priv)) {
				logger(DEBUG_ALWAYS, LOG_ERR, "unveil(%s, %s) failed: %s", p->path, p->priv, strerror(errno));
			}
		}
	}
}

bool restrict_privs(const char *promises, const char *execpromises) {
	if(pledge(promises, execpromises)) {
		logger(DEBUG_ALWAYS, LOG_ERR, "pledge(%s, %s) failed: %s", promises, execpromises, strerror(errno));
		return false;
	} else {
		return true;
	}
}


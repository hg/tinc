#include "unittest.h"

// Test that randomize() kills the process when called without initialization

#ifndef HAVE_GETRANDOM
#include "../../src/random.h"

static void on_abort(int sig) {
	(void)sig;
	exit(1);
}

int main(void) {
	signal(SIGABRT, on_abort);
	u_int8_t buf[16];
	randomize(buf, sizeof(buf));
	return 0;
}
#else
int main(void) {
	return 1;
}
#endif // HAVE_GETRANDOM

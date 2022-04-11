#include "system.h"
#include "random.h"

#ifndef HAVE_WINDOWS

#ifdef HAVE_GETRANDOM
void random_init(void) {}
void random_exit(void) {}
#else
static int random_fd = -1;

void random_init(void) {
	random_fd = open("/dev/urandom", O_RDONLY);

	if(random_fd < 0) {
		random_fd = open("/dev/random", O_RDONLY);
	}

	if(random_fd < 0) {
		fprintf(stderr, "Could not open source of random numbers: %s\n", strerror(errno));
		abort();
	}
}

void random_exit(void) {
	close(random_fd);
}
#endif

void randomize(void *vout, size_t outlen) {
	uint8_t *out = vout;

	while(outlen) {
#ifdef HAVE_GETRANDOM
		ssize_t len = getrandom(out, outlen, 0);
#else
		ssize_t len = read(random_fd, out, outlen);
#endif

		if(len <= 0) {
			if(len == -1 && (errno == EAGAIN || errno == EINTR)) {
				continue;
			}

			fprintf(stderr, "Could not read random numbers: %s\n", strerror(errno));
			abort();
		}

		out += len;
		outlen -= len;
	}
}

#else // HAVE_WINDOWS

#include <wincrypt.h>

static HCRYPTPROV prov;

void random_init(void) {
	if(!CryptAcquireContext(&prov, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)) {
		fprintf(stderr, "CryptAcquireContext() failed!\n");
		abort();
	}
}

void random_exit(void) {
	CryptReleaseContext(prov, 0);
}

void randomize(void *vout, size_t outlen) {
	if(!CryptGenRandom(prov, outlen, vout)) {
		fprintf(stderr, "CryptGenRandom() failed\n");
		abort();
	}
}

#endif // HAVE_WINDOWS

#include "../system.h"

#include "chacha.h"
#include "../xalloc.h"

//#if defined(__clang__)
//#  pragma clang attribute push (__attribute__((target("fpu=neon"))), apply_to=function)
//#elif defined(__GNUC__)

//#if defined(__GNUC__)
//#  pragma GCC target("fpu=neon")
//#endif

#include <arm_neon.h>

#define U8C(v) (v##U)
#define U32C(v) (v##U)

#define U8V(v) ((uint8_t)(v) & U8C(0xFF))
#define U32V(v) ((uint32_t)(v) & U32C(0xFFFFFFFF))

#define ROTL32(v, n) \
	(U32V((v) << (n)) | ((v) >> (32 - (n))))

#define U8TO32_LITTLE(p) \
	(((uint32_t)((p)[0])      ) | \
	 ((uint32_t)((p)[1]) <<  8) | \
	 ((uint32_t)((p)[2]) << 16) | \
	 ((uint32_t)((p)[3]) << 24))

#define U32TO8_LITTLE(p, v) \
	do { \
		(p)[0] = U8V((v)      ); \
		(p)[1] = U8V((v) >>  8); \
		(p)[2] = U8V((v) >> 16); \
		(p)[3] = U8V((v) >> 24); \
	} while (0)

#define ROTATE(v,c) (ROTL32(v,c))
#define XOR(v,w) ((v) ^ (w))
#define PLUS(v,w) (U32V((v) + (w)))
#define PLUSONE(v) (PLUS((v),1))

#define QUARTERROUND(a,b,c,d) \
	x[a] = PLUS(x[a],x[b]); x[d] = ROTATE(XOR(x[d],x[a]),16); \
	x[c] = PLUS(x[c],x[d]); x[b] = ROTATE(XOR(x[b],x[c]),12); \
	x[a] = PLUS(x[a],x[b]); x[d] = ROTATE(XOR(x[d],x[a]), 8); \
	x[c] = PLUS(x[c],x[d]); x[b] = ROTATE(XOR(x[b],x[c]), 7);

static void salsa20_wordtobyte(uint8_t output[64], const uint32_t input[16]) {
	uint32_t x[16];
	int i;

	for(i = 0; i < 16; ++i) {
		x[i] = input[i];
	}

	for(i = 20; i > 0; i -= 2) {
		QUARTERROUND(0, 4, 8, 12)
		QUARTERROUND(1, 5, 9, 13)
		QUARTERROUND(2, 6, 10, 14)
		QUARTERROUND(3, 7, 11, 15)
		QUARTERROUND(0, 5, 10, 15)
		QUARTERROUND(1, 6, 11, 12)
		QUARTERROUND(2, 7, 8, 13)
		QUARTERROUND(3, 4, 9, 14)
	}

	for(i = 0; i < 16; ++i) {
		x[i] = PLUS(x[i], input[i]);
	}

	for(i = 0; i < 16; ++i) {
		U32TO8_LITTLE(output + 4 * i, x[i]);
	}
}

void chacha_encrypt_bytes_neon(chacha_ctx *ctx, const uint8_t *m, uint8_t *out, uint32_t bytes) {
	uint32_t *x = &ctx->input[0];
	int i;

#include "chacha_neon.h"

	if(!bytes) {
		return;
	}

	uint8_t output[64];

	for(;;) {
		salsa20_wordtobyte(output, x);
		x[12] = PLUSONE(x[12]);

		if(!x[12]) {
			x[13] = PLUSONE(x[13]);
			/* stopping at 2^70 bytes per nonce is user's responsibility */
		}

		if(bytes <= 64) {
			for(i = 0; i < bytes; ++i) {
				out[i] = m[i] ^ output[i];
			}

			return;
		}

		for(i = 0; i < 64; ++i) {
			out[i] = m[i] ^ output[i];
		}

		bytes -= 64;
		out += 64;
		m += 64;
	}
}

//#ifdef __clang__
//#  pragma clang attribute pop
//#endif

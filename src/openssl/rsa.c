/*
    rsa.c -- RSA key handling
    Copyright (C) 2007-2022 Guus Sliepen <guus@tinc-vpn.org>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

#include "../system.h"

#include <openssl/pem.h>
#include <openssl/rsa.h>

#define TINC_RSA_INTERNAL

#if OPENSSL_VERSION_MAJOR < 3
typedef RSA rsa_t;
#else
#include <openssl/encoder.h>
#include <openssl/decoder.h>
#include <openssl/core_names.h>
#include <openssl/param_build.h>
#include <assert.h>

typedef EVP_PKEY rsa_t;
#endif

#include "log.h"
#include "../logger.h"
#include "../rsa.h"

// Set RSA keys

#if OPENSSL_VERSION_MAJOR >= 3
static EVP_PKEY *build_rsa_key(int selection, const BIGNUM *bn, const BIGNUM *be, const BIGNUM *bd) {
	assert(bn);
	assert(be);

	EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_from_name(NULL, "RSA", NULL);

	if(!ctx) {
		ssl_err("initialize key context");
		return NULL;
	}

	OSSL_PARAM_BLD *bld = OSSL_PARAM_BLD_new();
	OSSL_PARAM_BLD_push_BN(bld, OSSL_PKEY_PARAM_RSA_N, bn);
	OSSL_PARAM_BLD_push_BN(bld, OSSL_PKEY_PARAM_RSA_E, be);

	if(bd) {
		OSSL_PARAM_BLD_push_BN(bld, OSSL_PKEY_PARAM_RSA_D, bd);
	}

	OSSL_PARAM *params = OSSL_PARAM_BLD_to_param(bld);
	EVP_PKEY *key = NULL;

	bool ok = EVP_PKEY_fromdata_init(ctx) > 0
	          && EVP_PKEY_fromdata(ctx, &key, selection, params) > 0;

	OSSL_PARAM_free(params);
	OSSL_PARAM_BLD_free(bld);
	EVP_PKEY_CTX_free(ctx);

	if(ok) {
		return key;
	}

	ssl_err("build key");
	return NULL;
}
#endif

rsa_t *rsa_set_hex_public_key(const char *n, const char *e) {
	rsa_t *rsa = NULL;
	BIGNUM *bn_n = NULL;
	BIGNUM *bn_e = NULL;

	if((size_t)BN_hex2bn(&bn_n, n) != strlen(n) || (size_t)BN_hex2bn(&bn_e, e) != strlen(e)) {
		goto exit;
	}

#if OPENSSL_VERSION_MAJOR < 3
	rsa = RSA_new();

	if(rsa) {
		RSA_set0_key(rsa, bn_n, bn_e, NULL);
	}

#else
	rsa = build_rsa_key(EVP_PKEY_PUBLIC_KEY, bn_n, bn_e, NULL);
#endif

exit:
#if OPENSSL_VERSION_MAJOR < 3

	if(!rsa)
#endif
	{
		BN_free(bn_e);
		BN_free(bn_n);
	}

	return rsa;
}

rsa_t *rsa_set_hex_private_key(const char *n, const char *e, const char *d) {
	rsa_t *rsa = NULL;
	BIGNUM *bn_n = NULL;
	BIGNUM *bn_e = NULL;
	BIGNUM *bn_d = NULL;

	if((size_t)BN_hex2bn(&bn_n, n) != strlen(n) || (size_t)BN_hex2bn(&bn_e, e) != strlen(e) || (size_t)BN_hex2bn(&bn_d, d) != strlen(d)) {
		goto exit;
	}

#if OPENSSL_VERSION_MAJOR < 3
	rsa = RSA_new();

	if(rsa) {
		RSA_set0_key(rsa, bn_n, bn_e, bn_d);
	}

#else
	rsa = build_rsa_key(EVP_PKEY_KEYPAIR, bn_n, bn_e, bn_d);
#endif

exit:
#if OPENSSL_VERSION_MAJOR < 3

	if(!rsa)
#endif
	{
		BN_free(bn_d);
		BN_free(bn_e);
		BN_free(bn_n);
	}

	return rsa;
}

// Read PEM RSA keys

#if OPENSSL_VERSION_MAJOR >= 3
static rsa_t *read_key(FILE *fp, int selection) {
	rsa_t *rsa = NULL;
	OSSL_DECODER_CTX *ctx = OSSL_DECODER_CTX_new_for_pkey(&rsa, "PEM", NULL, "RSA", selection, NULL, NULL);

	if(!ctx) {
		ssl_err("initialize decoder");
		return NULL;
	}

	bool ok = OSSL_DECODER_from_fp(ctx, fp);
	OSSL_DECODER_CTX_free(ctx);

	if(!ok) {
		rsa = NULL;
		ssl_err("read RSA key from file");
	}

	return rsa;
}
#endif

rsa_t *rsa_read_pem_public_key(FILE *fp) {
	rsa_t *rsa;

#if OPENSSL_VERSION_MAJOR < 3
	rsa = PEM_read_RSAPublicKey(fp, NULL, NULL, NULL);

	if(!rsa) {
		rewind(fp);
		rsa = PEM_read_RSA_PUBKEY(fp, NULL, NULL, NULL);
	}

#else
	rsa = read_key(fp, OSSL_KEYMGMT_SELECT_PUBLIC_KEY);
#endif

	if(!rsa) {
		ssl_err("read RSA public key");
	}

	return rsa;
}

rsa_t *rsa_read_pem_private_key(FILE *fp) {
	rsa_t *rsa;

#if OPENSSL_VERSION_MAJOR < 3
	rsa = PEM_read_RSAPrivateKey(fp, NULL, NULL, NULL);
#else
	rsa = read_key(fp, OSSL_KEYMGMT_SELECT_PRIVATE_KEY);
#endif

	if(!rsa) {
		ssl_err("read RSA private key");
	}

	return rsa;
}

size_t rsa_size(const rsa_t *rsa) {
#if OPENSSL_VERSION_MAJOR < 3
	return RSA_size(rsa);
#else
	return EVP_PKEY_get_size(rsa);
#endif
}

bool rsa_public_encrypt(rsa_t *rsa, const void *in, size_t len, void *out) {
#if OPENSSL_VERSION_MAJOR < 3

	if((size_t)RSA_public_encrypt((int) len, in, out, rsa, RSA_NO_PADDING) == len) {
		return true;
	}

#else
	EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(rsa, NULL);

	if(ctx) {
		size_t outlen = len;

		bool ok = EVP_PKEY_encrypt_init(ctx) > 0
		          && EVP_PKEY_CTX_set_rsa_padding(ctx, RSA_NO_PADDING) > 0
		          && EVP_PKEY_encrypt(ctx, out, &outlen, in, len) > 0
		          && outlen == len;

		EVP_PKEY_CTX_free(ctx);

		if(ok) {
			return true;
		}
	}

#endif

	ssl_err("perform RSA encryption");
	return false;
}

bool rsa_private_decrypt(rsa_t *rsa, const void *in, size_t len, void *out) {
#if OPENSSL_VERSION_MAJOR < 3

	if((size_t)RSA_private_decrypt((int) len, in, out, rsa, RSA_NO_PADDING) == len) {
		return true;
	}

#else
	EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(rsa, NULL);

	if(ctx) {
		size_t outlen = len;

		bool ok = EVP_PKEY_decrypt_init(ctx) > 0
		          && EVP_PKEY_CTX_set_rsa_padding(ctx, RSA_NO_PADDING) > 0
		          && EVP_PKEY_decrypt(ctx, out, &outlen, in, len) > 0
		          && outlen == len;

		EVP_PKEY_CTX_free(ctx);

		if(ok) {
			return true;
		}
	}

#endif

	ssl_err("perform RSA decryption");
	return false;
}

void rsa_free(rsa_t *rsa) {
	if(rsa) {
#if OPENSSL_VERSION_MAJOR < 3
		RSA_free(rsa);
#else
		EVP_PKEY_free(rsa);
#endif
	}
}

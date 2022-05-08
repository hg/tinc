#ifndef TINC_LINUX_LANDLOCK_H
#define TINC_LINUX_LANDLOCK_H

#include "../system.h"

#ifdef HAVE_LINUX_LANDLOCK_H

#include <linux/landlock.h>

typedef struct landlock_path_t {
	const char *path;
	const uint64_t flags;
} landlock_path_t;

static const uint32_t FS_EXECUTE = LANDLOCK_ACCESS_FS_EXECUTE;
static const uint32_t FS_WRITE_FILE = LANDLOCK_ACCESS_FS_WRITE_FILE;
static const uint32_t FS_READ_FILE = LANDLOCK_ACCESS_FS_READ_FILE;
static const uint32_t FS_READ_DIR = LANDLOCK_ACCESS_FS_READ_DIR;
static const uint32_t FS_REMOVE_DIR = LANDLOCK_ACCESS_FS_REMOVE_DIR;
static const uint32_t FS_REMOVE_FILE = LANDLOCK_ACCESS_FS_REMOVE_FILE;
static const uint32_t FS_MAKE_CHAR = LANDLOCK_ACCESS_FS_MAKE_CHAR;
static const uint32_t FS_MAKE_DIR = LANDLOCK_ACCESS_FS_MAKE_DIR;
static const uint32_t FS_MAKE_REG = LANDLOCK_ACCESS_FS_MAKE_REG;
static const uint32_t FS_MAKE_SOCK = LANDLOCK_ACCESS_FS_MAKE_SOCK;
static const uint32_t FS_MAKE_FIFO = LANDLOCK_ACCESS_FS_MAKE_FIFO;
static const uint32_t FS_MAKE_BLOCK = LANDLOCK_ACCESS_FS_MAKE_BLOCK;
static const uint32_t FS_MAKE_SYM = LANDLOCK_ACCESS_FS_MAKE_SYM;

// Restrict access to paths using Landlock LSM (kernel 5.13+).
// Filters are inherited by child processes and cannot be removed.
// Paths not passed in the first call to this function will not be available after it returns.
// https://docs.kernel.org/userspace-api/landlock.html
extern bool allow_paths(const landlock_path_t paths[]);

#endif // HAVE_LINUX_LANDLOCK_H

#endif // TINC_LINUX_LANDLOCK_H

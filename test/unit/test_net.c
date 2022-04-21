#include "unittest.h"
#include "../../src/net.h"
#include "../../src/script.h"
#include "../../src/xalloc.h"

static environment_t *device_env = NULL;

// silence -Wmissing-prototypes
void __wrap_environment_init(environment_t *env);
void __wrap_environment_exit(environment_t *env);
bool __wrap_execute_script(const char *name, environment_t *env);

void __wrap_environment_init(environment_t *env) {
	assert_non_null(env);
	assert_null(device_env);
	device_env = env;
}

void __wrap_environment_exit(environment_t *env) {
	assert_ptr_equal(device_env, env);
	device_env = NULL;
}

bool __wrap_execute_script(const char *name, environment_t *env) {
	(void)env;

	check_expected_ptr(name);

	// Used instead of mock_type(bool) to silence clang warning
	return mock() ? true : false;
}

static void run_device_enable_disable(void (*device_func)(void),
                                      const char *script) {
	expect_string(__wrap_execute_script, name, script);
	will_return(__wrap_execute_script, true);

	device_func();
}

static void test_device_enable_calls_tinc_up(void **state) {
	(void)state;

	run_device_enable_disable(&device_enable, "tinc-up");
}

static void test_device_disable_calls_tinc_down(void **state) {
	(void)state;

	run_device_enable_disable(&device_disable, "tinc-down");
}

static void set_proxy(proxytype_t type, const char *host) {
	proxytype = type;
	free(proxyhost);

	if(host) {
		proxyhost = xstrdup(host);
	} else {
		proxyhost = NULL;
	}
}

static void test_proxy_exe_returns_null_on_wrong_proxytype(void **state) {
	(void)state;

	for(proxytype_t type = PROXY_NONE; type != PROXY_EXEC; ++type) {
		set_proxy(type, "foobar");
		assert_null(proxy_exe());
	}
}

static void test_proxy_exe_returns_null_on_wrong_command(void **state) {
	(void)state;

	set_proxy(PROXY_EXEC, "");
	assert_null(proxy_exe());

	set_proxy(PROXY_EXEC, "   \t\r\n ");
	assert_null(proxy_exe());

	set_proxy(PROXY_EXEC, NULL);
	assert_null(proxy_exe());
}

static void check_proxy(const char *input, const char *want) {
	set_proxy(PROXY_EXEC, input);
	char *get = proxy_exe();
	assert_string_equal(want, get);
	free(get);
}

static void test_proxy_exe_returns_valid_command(void **state) {
	(void)state;

	check_proxy("foo bar baz", "foo");
	check_proxy(" \n\r\t dir/frobnicator\\1.4-2 | tee -a --moo 9000 ", "dir/frobnicator\\1.4-2");
}

static int teardown_proxy(void **state) {
	(void)state;
	free(proxyhost);
	proxyhost = NULL;
	return 0;
}

int main(void) {
	const struct CMUnitTest tests[] = {
		cmocka_unit_test(test_device_enable_calls_tinc_up),
		cmocka_unit_test(test_device_disable_calls_tinc_down),
		cmocka_unit_test(test_proxy_exe_returns_null_on_wrong_command),
		cmocka_unit_test_teardown(test_proxy_exe_returns_null_on_wrong_proxytype, teardown_proxy),
		cmocka_unit_test_teardown(test_proxy_exe_returns_valid_command, teardown_proxy),
	};
	return cmocka_run_group_tests(tests, NULL, NULL);
}

#include "unittest.h"
#include "../../src/random.h"

static int setup(void **state) {
	(void)state;
	random_init();
	return 0;
}

static int teardown(void **state) {
	(void)state;
	random_exit();
	return 0;
}

static const uint8_t ref[128] = {0};

static void test_randomize_zero_must_not_change_memory(void **state) {
	(void)state;

	uint8_t data[sizeof(ref)] = {0};
	randomize(data, 0);

	assert_memory_equal(ref, data, sizeof(data));
}

static void test_randomize_half_changes_half(void **state) {
	(void)state;

	uint8_t data[sizeof(ref)] = {0};
	const size_t half = sizeof(data) / 2;
	randomize(data, half);

	assert_memory_not_equal(data, ref, half);
	assert_memory_equal(&data[half], ref, half);
}

static void test_randomize_full_changes_memory(void **state) {
	(void)state;

	uint8_t data[sizeof(ref)] = {0};
	randomize(data, sizeof(data));

	assert_memory_not_equal(ref, data, sizeof(data));
}

int main(void) {
	const struct CMUnitTest tests[] = {
		cmocka_unit_test(test_randomize_zero_must_not_change_memory),
		cmocka_unit_test(test_randomize_half_changes_half),
		cmocka_unit_test(test_randomize_full_changes_memory),
	};
	return cmocka_run_group_tests(tests, setup, teardown);
}

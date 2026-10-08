CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Werror -fno-fast-math
BUILD_DIR ?= build
.PHONY: all test clean
all: $(BUILD_DIR)/libchimera_nbit.a
$(BUILD_DIR):
	mkdir -p $@
$(BUILD_DIR)/chimera_nbit_runtime.o: chimera_nbit_runtime.c chimera_nbit_runtime.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/libchimera_nbit.a: $(BUILD_DIR)/chimera_nbit_runtime.o
	$(AR) rcs $@ $<
$(BUILD_DIR)/test_runtime: chimera_nbit_runtime.c test_runtime.c chimera_nbit_runtime.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) chimera_nbit_runtime.c test_runtime.c -o $@
test: $(BUILD_DIR)/test_runtime
	./$(BUILD_DIR)/test_runtime
clean:
	rm -rf $(BUILD_DIR)

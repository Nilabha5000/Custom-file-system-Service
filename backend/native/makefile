# Compiler
CC = gcc

# Project name
TARGET = fslib

# Directories
SRC_DIR = src
INC_DIR = include
BUILD_DIR = build

# Source files
SRCS = $(wildcard $(SRC_DIR)/*.c)

# Output files
LINUX_LIB = $(BUILD_DIR)/lib$(TARGET).so
WIN_LIB   = $(BUILD_DIR)/$(TARGET).dll

# Flags
CFLAGS = -Wall -Wextra -O2 -fPIC -I$(INC_DIR)
LDFLAGS = -shared

# Default target
all: linux

# Build for Linux
linux: $(LINUX_LIB)

$(LINUX_LIB): $(SRCS)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@

# Build for Windows (MinGW)
windows: $(WIN_LIB)

$(WIN_LIB): $(SRCS)
	@mkdir -p $(BUILD_DIR)
	$(CC) -shared -I$(INC_DIR) $^ -o $@

# Clean build files
clean:
	rm -rf $(BUILD_DIR)

# Rebuild everything
rebuild: clean all

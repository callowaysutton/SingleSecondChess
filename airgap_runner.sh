#!/bin/bash

# Airgapped Runner Script for Debian 12
set -euo pipefail

# Function to print error messages and exit
function error_exit {
    echo "Error: $1" >&2
    exit 1
}

# Ensure required commands are available
REQUIRED_CMDS=("bwrap" "taskset" "ldd" "cp" "mkdir" "which" "readlink" "find")
for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        error_exit "Required command '$cmd' is not available. Please install it and try again."
    fi
done

# Define variables
JAIL_DIR="jail"
BINARY_DIR="$JAIL_DIR/bin"
LIB_DIRS=("$JAIL_DIR/lib" "$JAIL_DIR/lib64" "$JAIL_DIR/usr/lib" "$JAIL_DIR/usr/lib64")
PROGRAMS=("./wrapper" "./p1" "./p2" "$(which perf)" "$(which timeout)" "/bin/sh")

# Clean up existing jail directory if it exists
if [ -d "$JAIL_DIR" ]; then
    echo "Removing existing jail directory..."
    rm -rf "$JAIL_DIR"
fi

# Create necessary directories
echo "Creating jail directories..."
mkdir -p "$BINARY_DIR"
for dir in "${LIB_DIRS[@]}"; do
    mkdir -p "$dir"
done
mkdir -p "$JAIL_DIR/dev" "$JAIL_DIR/tmp"

# Create necessary device files
echo "Creating device files..."
mknod -m 666 "$JAIL_DIR/dev/null" c 1 3
mknod -m 666 "$JAIL_DIR/dev/zero" c 1 5
mknod -m 666 "$JAIL_DIR/dev/random" c 1 8
mknod -m 666 "$JAIL_DIR/dev/urandom" c 1 9

# Verify that all required programs exist and are executable
for prog in "${PROGRAMS[@]}"; do
    if [ ! -x "$prog" ]; then
        error_exit "Program '$prog' not found or not executable."
    fi
done

# Copy binaries into the jail
echo "Copying binaries into jail..."
for prog in "${PROGRAMS[@]}"; do
    cp -v "$prog" "$BINARY_DIR/"
done

# Function to copy library dependencies
copy_dependencies() {
    local binary="$1"
    echo "Processing dependencies for $binary..."

    ldd "$binary" | awk '/=>/ { print $3 }' | while read -r lib; do
        if [ -z "$lib" ] || [ ! -e "$lib" ]; then
            continue
        fi
        lib_dest="$JAIL_DIR$lib"
        lib_dir="$(dirname "$lib_dest")"
        mkdir -p "$lib_dir"
        if [ ! -e "$lib_dest" ]; then
            cp -v "$lib" "$lib_dest"
        fi
    done
}

# Copy dependencies for each binary
for prog in "${PROGRAMS[@]}"; do
    copy_dependencies "$prog"
done

# Copy the dynamic linker/loader
LOADER="$(ldd "${PROGRAMS[0]}" | grep 'ld-linux' | awk '{ print $1 }')"
if [ -z "$LOADER" ] || [ ! -e "$LOADER" ]; then
    LOADER="/lib64/ld-linux-x86-64.so.2"
    if [ ! -e "$LOADER" ]; then
        error_exit "Dynamic linker/loader not found."
    fi
fi
LOADER_DEST="$JAIL_DIR$LOADER"
LOADER_DIR="$(dirname "$LOADER_DEST")"
mkdir -p "$LOADER_DIR"
cp -v "$LOADER" "$LOADER_DEST"

# Handle symlinks for libraries
echo "Processing symlinks..."
find "$JAIL_DIR" -type l | while read -r symlink; do
    target="$(readlink "$symlink")"
    if [[ "$target" = /* ]]; then
        new_target="$JAIL_DIR$target"
        if [ -e "$new_target" ]; then
            ln -sf "$target" "$symlink"
        else
            echo "Warning: Target $target for symlink $symlink does not exist in jail."
        fi
    fi
done

# Mount /proc and /tmp inside the sandbox
echo "Executing the program in the airgapped environment..."
bwrap \
    --die-with-parent \
    --bind /etc/localtime /etc/localtime \
    --bind "$PWD/$JAIL_DIR" / \
    --dev-bind /dev /dev \
    --proc /proc \
    --tmpfs /tmp \
    --chdir / \
    /bin/wrapper

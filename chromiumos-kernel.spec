# === FIX: Disable automatic stripping ===
# This is CRITICAL. Without this, rpmbuild runs 'brp-strip' which destroys
# the kernel image (vmlinuz) header, causing "kernel DOS magic is invalid" boot errors.
%global __os_install_post %{nil}

# Disable debuginfo packages (optional, but keeps build smaller)
%global _enable_debug_package 0
%global debug_package %{nil}

Name:       chromiumos-kernel
Version:    6.1.145
Release:    1%{?dist}
Summary:    The Linux kernel from Chromium OS
License:    GPLv2
URL:        https://chromium.googlesource.com/chromiumos/third_party/kernel

Conflicts:  kernel
Conflicts:  kernel-core
Conflicts:  kernel-modules
Conflicts:  kernel-modules-core

Provides:   kernel = %{version}-%{release}
Provides:   kernel-core = %{version}-%{release}
Provides:   kernel-modules = %{version}-%{release}
Provides:   kernel-modules-core = %{version}-%{release}
Provides:   kernel-uname-r = %{version}-%{release}.%{_arch}

# This must match the tarball name created by your Makefile
Source0:    linux-chromiumos.tar.xz

BuildRequires:  gcc, make, flex, bison, openssl-devel, elfutils-libelf-devel, dwarves
BuildRequires:  bc, perl-interpreter, git
# FIX: Added python3 because chromeos build scripts require it
BuildRequires:  python3
# FIX: Added lzma command because Chromium kernels use CONFIG_KERNEL_LZMA
BuildRequires:  /usr/bin/lzma
# FIX: Added kmod because 'make modules_install' requires depmod
BuildRequires:  kmod
# FIX: Added xz to compress symvers
BuildRequires:  xz

%description
This is the Linux kernel built from the Chromium OS source tree.

%prep
# Unpack the source; 'chromium-kernel' matches the directory name inside the tarball
%setup -q -n chromium-kernel

%build
# FIX 1: Export the required environment variable
export CHROMEOS_KERNEL_FAMILY=chromeos

# Clean up any stale configs
make mrproper

# Force the modules to be installed in /lib/modules/6.1.145-chromiumos
./scripts/config --set-str CONFIG_LOCALVERSION "-chromiumos"

# FIX 2: Use the specific flavor found in your screenshot
# 'chromiumos-x86_64-generic' corresponds to chromiumos-x86_64-generic.flavour.config
./chromeos/scripts/prepareconfig chromiumos-x86_64-generic

# FIX 3: Disable Werror to prevent failures on newer Fedora GCC versions
./scripts/config --disable CONFIG_WERROR

# FIX 4: Patch Makefiles to force C11 standard (fixing C23 bool/false errors)
# Fedora GCC defaults to C23, breaking legacy kernel code.
# KCFLAGS isn't enough because realmode/boot code ignores it.

# 4a. Force standard for host tools (fix libbpf/tools errors)
sed -i 's/^HOSTCFLAGS\s*:=/HOSTCFLAGS\t:= -std=gnu11 /' Makefile

# 4b. Force standard for x86 Realmode boot code (fix wakemain.c errors)
sed -i 's/^REALMODE_CFLAGS\s*:=/REALMODE_CFLAGS\t:= -std=gnu11 /' arch/x86/Makefile

# Ensure the config is updated for the current kernel version without user prompts
./scripts/config --set-str CONFIG_LOCALVERSION "-chromiumos"
make olddefconfig

# Compile the kernel image and modules
# WERROR=0 provides an extra safety net
# We keep the flags here too as a backup for the main kernel objects
make %{?_smp_mflags} WERROR=0 \
    KCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    HOSTCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    bzImage modules

%install
# Create the directory structure in the buildroot
mkdir -p %{buildroot}/boot
mkdir -p %{buildroot}/lib/modules

# Install kernel modules to the buildroot
# DEPMOD=/bin/true prevents depmod from running during the build (it runs on the target system instead)
make modules_install INSTALL_MOD_PATH=%{buildroot} DEPMOD=/bin/true

# Install the kernel image with the version suffix (Required for standard Fedora structure)
install -D -m 755 arch/x86/boot/bzImage %{buildroot}/lib/modules/%{version}-chromiumos/vmlinuz-%{version}-chromiumos

# Install System.map and config with the version suffix
install -D -m 644 System.map %{buildroot}/lib/modules/%{version}-chromiumos/System.map-%{version}-chromiumos
install -D -m 644 .config %{buildroot}/lib/modules/%{version}-chromiumos/config-%{version}-chromiumos

# NEW: Compress and install Module.symvers
# This is required for building external modules (DKMS) later
xz -c Module.symvers > %{buildroot}/lib/modules/%{version}-chromiumos/symvers.xz
chmod 644 %{buildroot}/lib/modules/%{version}-chromiumos/symvers.xz

# Cleanup: Remove 'build' and 'source' symlinks that point to the build environment
rm -f %{buildroot}/lib/modules/*/build
rm -f %{buildroot}/lib/modules/*/source

# Note: We removed the "Save/Restore Unstripped" macros because disabling
# __os_install_post at the top of the file handles this more reliably.

%post
# Triggers kernel-install to create the initramfs and update bootloader entries
# The kernel version argument must match the directory name in /lib/modules/
/bin/kernel-install add %{version}-chromiumos /lib/modules/%{version}-chromiumos/vmlinuz-%{version}-chromiumos || :

%preun
# Removes the kernel from bootloader entries and deletes initramfs upon uninstallation
/bin/kernel-install remove %{version}-chromiumos || :

%posttrans
# Ensures everything is clean after the transaction
/bin/kernel-install add %{version}-chromiumos /lib/modules/%{version}-chromiumos/vmlinuz-%{version}-chromiumos || :

%files
# This wildcard covers vmlinuz, config, System.map, symvers.xz, and the 'kernel' directory
/lib/modules/%{version}-chromiumos/

%changelog
* Mon Dec 01 2025 User <user@example.com> - 6.6-1
- Initial build
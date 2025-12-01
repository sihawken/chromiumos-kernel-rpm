Name:       kernel-chromiumos
Version:    6.6
Release:    1%{?dist}
Summary:    The Linux kernel from Chromium OS
License:    GPLv2
URL:        https://chromium.googlesource.com/chromiumos/third_party/kernel

# This must match the tarball name created by your Makefile
Source0:    linux-chromiumos.tar.xz

BuildRequires:  gcc, make, flex, bison, openssl-devel, elfutils-libelf-devel, dwarves
BuildRequires:  bc, perl-interpreter, git
# FIX: Added python3 because chromeos build scripts require it
BuildRequires:  python3

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

# FIX 2: Use the specific flavor found in your screenshot
# 'chromiumos-x86_64-generic' corresponds to chromiumos-x86_64-generic.flavour.config
./chromeos/scripts/prepareconfig chromiumos-x86_64-generic

# FIX 3: Disable Werror to prevent failures on newer Fedora GCC versions
# This handles the "discards 'const' qualifier" error in libbpf
./scripts/config --disable CONFIG_WERROR

# Ensure the config is updated for the current kernel version without user prompts
make olddefconfig

# Compile the kernel image and modules
# WERROR=0 provides an extra safety net for tools built during the process
# KCFLAGS and HOSTCFLAGS added to suppress specific libbpf const errors on newer GCC
# FIX 4: Added -std=gnu11 to KCFLAGS and HOSTCFLAGS. 
# Fedora GCC defaults to C23 which breaks kernel bool/false typedefs.
make %{?_smp_mflags} WERROR=0 \
    KCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    HOSTCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    bzImage modules

%install
mkdir -p %{buildroot}/boot
mkdir -p %{buildroot}/lib/modules

# Install modules
make modules_install INSTALL_MOD_PATH=%{buildroot}

# Install the kernel image
cp arch/x86/boot/bzImage %{buildroot}/boot/vmlinuz-%{version}-chromiumos
cp System.map %{buildroot}/boot/System.map-%{version}-chromiumos
cp .config %{buildroot}/boot/config-%{version}-chromiumos

# Cleanup firmware to avoid conflicts with linux-firmware package
rm -rf %{buildroot}/lib/firmware

%files
/lib/modules/*
/boot/vmlinuz*
/boot/System.map*
/boot/config*

%changelog
* Mon Dec 01 2025 User <user@example.com> - 6.6-1
- Initial build
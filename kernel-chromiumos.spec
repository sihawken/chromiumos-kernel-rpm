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

# FIX 2: Use the Chromium OS specific config script
# Adjust 'chromiumos-x86_64' to your target architecture if different (e.g., chromiumos-arm64)
# This script sets up the .config file based on ChromeOS defaults
./chromeos/scripts/prepareconfig chromiumos-x86_64

# Ensure the config is updated for the current kernel version without user prompts
make olddefconfig

# Compile the kernel image and modules
make %{?_smp_mflags} bzImage modules

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
# Using Mon Dec 01 2025 (today's date relative to the example) to pass validation.
* Mon Dec 01 2025 User <user@example.com> - 6.6-1
- Initial build
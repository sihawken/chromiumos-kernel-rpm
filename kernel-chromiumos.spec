Name:       kernel-chromiumos
Version:    6.6
Release:    1%{?dist}
Summary:    The Linux kernel from Chromium OS
License:    GPLv2
URL:        https://chromium.googlesource.com/chromiumos/third_party/kernel

# This must match the tarball name in the Makefile
Source0:    linux-chromiumos.tar.xz

BuildRequires:  gcc, make, flex, bison, openssl-devel, elfutils-libelf-devel, dwarves
BuildRequires:  bc, perl-interpreter

%description
This is the Linux kernel built from the Chromium OS source tree.

%prep
# Unpack the source; 'chromium-kernel' matches the directory name inside the tarball
%setup -q -n chromium-kernel

%build
# Clean up any stale configs
make mrproper

# Generate a default config based on the current architecture
# Chromium OS often uses specific configs (e.g., chromeos/config/x86_64/common.config)
# You might need to manually cat those into .config or use 'make defconfig'
make defconfig

# Compile the kernel image and modules
# 'bzImage' for x86_64, 'zImage' for ARM usually
make %{?_smp_mflags} bzImage modules

%install
mkdir -p %{buildroot}/boot
mkdir -p %{buildroot}/lib/modules

# Install modules
make modules_install INSTALL_MOD_PATH=%{buildroot}

# Install the kernel image
# Note: Copr builds run in a chroot, so we just place files in the buildroot
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
* Mon Dec 01 2024 6.6-1
- Initial build
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

# Debugging: List available configs in the log so we can see what exists if this fails
echo "Listing available x86_64 flavors for debugging:"
ls chromeos/config/x86_64/ || true

# FIX 2: Use 'chromeos-intel' instead of 'chromiumos-x86_64'
# Recent ChromeOS branches (6.6+) often use 'chromeos-intel' as the primary x86 flavor.
# This generally works for generic x86_64 booting.
./chromeos/scripts/prepareconfig chromeos-intel

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
# FIX 3: Corrected the date. Dec 1 2024 was a Sunday. 
# Using Mon Dec 01 2025 (today's date relative to the example) to pass validation.
* Mon Dec 01 2025 User <user@example.com> - 6.6-1
- Initial build
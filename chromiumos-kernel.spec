# FIX: Disable debuginfo package generation to prevent "Empty %files file" errors
%global debug_package %{nil}

Name:       chromiumos-kernel
# Matches the specific version from your source tree (6.1.145)
Version:    6.1.145
Release:    1%{?dist}
Summary:    The Linux kernel from Chromium OS
License:    GPLv2
URL:        https://chromium.googlesource.com/chromiumos/third_party/kernel

# -----------------------------------------------------------------------------
# CRITICAL CONFIGURATION: SINGLE KERNEL MODE
# -----------------------------------------------------------------------------
# 1. CONFLICTS: Explicitly conflict with stock Fedora kernels.
#    WARNING: Installing this will REMOVE kernel, kernel-core, and kernel-modules.
Conflicts:  kernel
Conflicts:  kernel-core
Conflicts:  kernel-modules

# 2. PROVIDES: essential virtual packages to satisfy dependencies
Provides:   kernel = %{version}-%{release}
Provides:   kernel-core = %{version}-%{release}
Provides:   kernel-modules = %{version}-%{release}
Provides:   kernel-uname-r = %{version}-%{release}.%{_arch}
# -----------------------------------------------------------------------------

Source0:    linux-chromiumos.tar.xz

BuildRequires:  gcc, make, flex, bison, openssl-devel, elfutils-libelf-devel, dwarves
BuildRequires:  bc, perl-interpreter, git
BuildRequires:  python3
BuildRequires:  /usr/bin/lzma
BuildRequires:  kmod
# Runtime dependencies required for creating initramfs
Requires:       coreutils, kmod, dracut, binutils, systemd-udev

%description
This is the Linux kernel built from the Chromium OS source tree.
This package replaces the standard system kernel.

%prep
%setup -q -n chromium-kernel

%build
export CHROMEOS_KERNEL_FAMILY=chromeos
make mrproper
./chromeos/scripts/prepareconfig chromiumos-x86_64-generic
./scripts/config --disable CONFIG_WERROR

# Patch Makefiles for GCC 15/C11 compatibility
sed -i 's/^HOSTCFLAGS\s*:=/HOSTCFLAGS\t:= -std=gnu11 /' Makefile
sed -i 's/^REALMODE_CFLAGS\s*:=/REALMODE_CFLAGS\t:= -std=gnu11 /' arch/x86/Makefile

make olddefconfig
make %{?_smp_mflags} WERROR=0 \
    KCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    HOSTCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    bzImage modules

%install
# Create the standard directory structure
mkdir -p %{buildroot}/lib/modules/%{version}

# Install modules
make modules_install INSTALL_MOD_PATH=%{buildroot}

# FIX: Install kernel image to /lib/modules/%{version}/vmlinuz
# This is the modern Fedora standard. kernel-install will copy it to /boot.
install -D -m 755 arch/x86/boot/bzImage %{buildroot}/lib/modules/%{version}/vmlinuz
cp System.map %{buildroot}/lib/modules/%{version}/System.map
cp .config %{buildroot}/lib/modules/%{version}/config

# Cleanup firmware
rm -rf %{buildroot}/lib/firmware

# Fix symlinks: Make them point to /dev/null or remove them to avoid build errors
# We will mark them as %ghost in the %files section
rm -f %{buildroot}/lib/modules/%{version}/build
rm -f %{buildroot}/lib/modules/%{version}/source
touch %{buildroot}/lib/modules/%{version}/build
touch %{buildroot}/lib/modules/%{version}/source

%files
%dir /lib/modules/%{version}
/lib/modules/%{version}/kernel
/lib/modules/%{version}/modules.*
/lib/modules/%{version}/vmlinuz
/lib/modules/%{version}/System.map
/lib/modules/%{version}/config
# Ghost files (owned by package but not shipped with content)
%ghost /lib/modules/%{version}/build
%ghost /lib/modules/%{version}/source
# We also ghost the initramfs so RPM knows it belongs to us after creation
%ghost /boot/initramfs-%{version}.img

%post
# 1. Generate module dependencies immediately so dracut can find them
/sbin/depmod -a %{version}

# 2. Add the kernel (triggers dracut to build initramfs)
# SKIP if running on an ostree system (rpm-ostree handles this automatically)
if [ ! -e /run/ostree-booted ]; then
    /bin/kernel-install add %{version} /lib/modules/%{version}/vmlinuz || :
fi

%preun
if [ $1 -eq 0 ]; then
    # SKIP removal on ostree systems
    if [ ! -e /run/ostree-booted ]; then
        /bin/kernel-install remove %{version} || :
    fi
fi

%posttrans
# Re-run kernel-install to ensure bootloader is updated if something changed
# SKIP if running on an ostree system
if [ ! -e /run/ostree-booted ]; then
    /bin/kernel-install add %{version} /lib/modules/%{version}/vmlinuz || :
fi

%changelog
* Mon Dec 01 2025 User <user@example.com> - 6.1.145-1
- Initial build
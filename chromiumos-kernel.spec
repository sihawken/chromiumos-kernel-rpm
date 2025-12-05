# ----------------------------------------------------------------------
# COPY FROM KERNEL.SPEC: Build Flags & Save/Restore Macros
# ----------------------------------------------------------------------

# Disable LTO and frame pointers to prevent boot stub corruption
%define _with_baseonly 1
%undefine _include_frame_pointers
%global _lto_cflags %{nil}

# Define the location to save unstripped binaries
%define buildroot_unstripped %{_builddir}/root_unstripped

# Macro to save a file from buildroot to the unstripped directory
%define buildroot_save_unstripped() \
(cd %{buildroot}; cp -rav --parents -t %{buildroot_unstripped}/ %1 || true) \
%{nil}

# Macro to restore the unstripped files back to buildroot
%define __restore_unstripped_root_post \
    echo "Restoring unstripped artefacts %{buildroot_unstripped} -> %{buildroot}" \
    cp -rav %{buildroot_unstripped}/. %{buildroot}/ \
%{nil}

# Override the standard install_post script.
# CRITICAL: We run the standard __os_install_post (which strips files) 
# and THEN run our restore script to overwrite the stripped kernel with the original.
%define __spec_install_post \
    %{?__debug_package:%{__debug_install_post}}\
    %{__arch_install_post}\
    %{__os_install_post}\
    %{__restore_unstripped_root_post}

# ----------------------------------------------------------------------

# Disable debuginfo packages (we are handling stripping manually via save/restore)
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

Source0:    linux-chromiumos.tar.xz

BuildRequires:  gcc, make, flex, bison, openssl, openssl-devel, elfutils-libelf-devel, dwarves
BuildRequires:  bc, perl-interpreter, git
BuildRequires:  python3
BuildRequires:  /usr/bin/lzma
BuildRequires:  kmod
BuildRequires:  xz

%description
This is the Linux kernel built from the Chromium OS source tree.

%prep
%setup -q -n chromium-kernel

%build
export CHROMEOS_KERNEL_FAMILY=chromeos

# Clean up any stale configs
make mrproper

# Force the modules to be installed in /lib/modules/6.1.145-chromiumos
./scripts/config --set-str CONFIG_LOCALVERSION "-chromiumos"

# Prepare config
./chromeos/scripts/prepareconfig chromeos-x86_64-reven

# Disable Werror
./scripts/config --disable CONFIG_WERROR

# Leave lockdown optional
./scripts/config --disable CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY
./scripts/config --enable CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE

# Enable virtualization
./scripts/config --enable CONFIG_KVM
./scripts/config --enable CONFIG_KVM_X86

# Enable ztsd kernel compression
./scripts/config --enable CONFIG_RD_ZSTD

# Filesystem
./scripts/config --enable CONFIG_BTRFS_FS
./scripts/config --enable CONFIG_XFS_FS
./scripts/config --enable CONFIG_EXT4_FS

# Compatibility
./scripts/config --disable CONFIG_MODULE_SIG_FORCE
./scripts/config --disable CONFIG_RESET_ATTACK_MITIGATION
./scripts/config --disable CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY

# Set LSM
./scripts/config --set-str CONFIG_LSM "lockdown,yama,integrity,selinux,bpf,landlock,ipe"
# Enable BPF LSM (Fedora standard)
./scripts/config --enable CONFIG_BPF_LSM
# Enable Integrity Policy Enforcement (Fedora standard)
./scripts/config --enable CONFIG_SECURITY_IPE

# [FIX] Enable text console output for Fedora
./scripts/config --enable CONFIG_VT
./scripts/config --enable CONFIG_VT_CONSOLE
./scripts/config --enable CONFIG_FRAMEBUFFER_CONSOLE

./scripts/config --enable CONFIG_FB
./scripts/config --enable CONFIG_FB_VGA16
./scripts/config --enable CONFIG_FB_VESA
./scripts/config --enable CONFIG_FB_EFI

./scripts/config --enable CONFIG_BLK_DEV_INITRD

# Core NVMe Support (Modules)
./scripts/config --enable CONFIG_NVME_KEYRING
./scripts/config --enable CONFIG_NVME_AUTH
./scripts/config --enable CONFIG_NVME_CORE
./scripts/config --enable CONFIG_BLK_DEV_NVME

# NVMe Features (Built-in)
./scripts/config --enable CONFIG_NVME_MULTIPATH
./scripts/config --enable CONFIG_NVME_HWMON

# NVMe Fabrics (Modules)
./scripts/config --module CONFIG_NVME_FABRICS
./scripts/config --module CONFIG_NVME_RDMA
./scripts/config --module CONFIG_NVME_FC
./scripts/config --module CONFIG_NVME_TCP

# NVMe Security (Built-in)
./scripts/config --enable CONFIG_NVME_TCP_TLS
./scripts/config --enable CONFIG_NVME_HOST_AUTH

# NVMe Target Support (Modules)
./scripts/config --module CONFIG_NVME_TARGET

# NVMe Target Features (Built-in)
./scripts/config --enable CONFIG_NVME_TARGET_PASSTHRU

# NVMe Target Transports (Modules)
./scripts/config --module CONFIG_NVME_TARGET_LOOP
./scripts/config --module CONFIG_NVME_TARGET_RDMA
./scripts/config --module CONFIG_NVME_TARGET_FC
./scripts/config --module CONFIG_NVME_TARGET_FCLOOP
./scripts/config --module CONFIG_NVME_TARGET_TCP

# NVMe Target Security (Built-in)
./scripts/config --enable CONFIG_NVME_TARGET_TCP_TLS
./scripts/config --enable CONFIG_NVME_TARGET_AUTH

# [FIX] Enable NVMe over PCIe (Critical for internal NVMe drives)
./scripts/config --enable CONFIG_PCIE_DW
./scripts/config --enable CONFIG_PCIE_DW_PLATFORM

# [FIX] Ensure the kernel can scan the PCI bus for drives
./scripts/config --enable CONFIG_PCI_MSI

# Fix Makefiles for C11 standard
echo "HOSTCFLAGS += -std=gnu11" >> Makefile
echo "REALMODE_CFLAGS += -std=gnu11" >> arch/x86/Makefile

./scripts/config --set-str CONFIG_LOCALVERSION "-chromiumos"
make olddefconfig

# Compile
make %{?_smp_mflags} WERROR=0 \
    KCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    HOSTCFLAGS="-Wno-error=discarded-qualifiers -std=gnu11" \
    bzImage modules

%install
# Create the directory structure in the buildroot
mkdir -p %{buildroot}/lib/modules/%{version}-chromiumos

# Install kernel modules
make modules_install INSTALL_MOD_PATH=%{buildroot}

# Install the kernel image using standard name 'vmlinuz'
install -D -m 755 arch/x86/boot/bzImage %{buildroot}/lib/modules/%{version}-chromiumos/vmlinuz

# Install System.map and config using standard names
install -D -m 644 System.map %{buildroot}/lib/modules/%{version}-chromiumos/System.map
install -D -m 644 .config %{buildroot}/lib/modules/%{version}-chromiumos/config

# Compress and install Module.symvers
xz -c Module.symvers > %{buildroot}/lib/modules/%{version}-chromiumos/symvers.xz
chmod 644 %{buildroot}/lib/modules/%{version}-chromiumos/symvers.xz

# Cleanup symlinks
rm -f %{buildroot}/lib/modules/*/build
rm -f %{buildroot}/lib/modules/*/source

# SAVE UNSTRIPPED KERNEL
# 1. Create the storage directory (fixes "cp: cannot stat" error)
mkdir -p %{buildroot_unstripped}
# 2. Save the vmlinuz file. This copy will be used to restore the file after RPM strips the original.
%buildroot_save_unstripped "lib/modules/%{version}-chromiumos/vmlinuz"

%post
/bin/kernel-install add %{version}-chromiumos /lib/modules/%{version}-chromiumos/vmlinuz || :

%preun
/bin/kernel-install remove %{version}-chromiumos || :

%posttrans
/bin/kernel-install add %{version}-chromiumos /lib/modules/%{version}-chromiumos/vmlinuz || :

%files
/lib/modules/%{version}-chromiumos/

%changelog
* Mon Dec 01 2025 User <user@example.com> - 6.6-1
- Initial build
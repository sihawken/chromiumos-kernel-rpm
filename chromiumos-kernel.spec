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

# Core Infrastructure & Initramfs
./scripts/config --enable CONFIG_BLOCK
./scripts/config --enable CONFIG_BLK_DEV_DM
./scripts/config --enable CONFIG_BLK_DEV_DM_BUILTIN
./scripts/config --enable CONFIG_BLK_DEV_INITRD
./scripts/config --enable CONFIG_CDROM
./scripts/config --enable CONFIG_MD
./scripts/config --enable CONFIG_MD_AUTODETECT
./scripts/config --enable CONFIG_MD_BITMAP_FILE
./scripts/config --enable CONFIG_PARTITION_ADVANCED
./scripts/config --enable CONFIG_RD_BZIP2
./scripts/config --enable CONFIG_RD_GZIP
./scripts/config --enable CONFIG_RD_LZO
./scripts/config --enable CONFIG_RD_LZ4
./scripts/config --enable CONFIG_RD_LZMA
./scripts/config --enable CONFIG_RD_XZ
./scripts/config --enable CONFIG_RD_ZSTD

# I/O Schedulers
./scripts/config --enable CONFIG_BFQ_GROUP_IOSCHED
./scripts/config --enable CONFIG_IOSCHED_BFQ
./scripts/config --enable CONFIG_MQ_IOSCHED_DEADLINE
./scripts/config --enable CONFIG_MQ_IOSCHED_KYBER

# SCSI/SATA/ATA
./scripts/config --module CONFIG_ATA_GENERIC        # CFL uses 'm', CRO uses 'y'
./scripts/config --module CONFIG_ATA_OVER_ETH
./scripts/config --enable CONFIG_BLK_DEV_BSG
./scripts/config --enable CONFIG_BLK_DEV_SD
./scripts/config --enable CONFIG_BLK_DEV_SR
./scripts/config --module CONFIG_CHR_DEV_SCH
./scripts/config --enable CONFIG_CHR_DEV_SG
./scripts/config --module CONFIG_CHR_DEV_ST
./scripts/config --module CONFIG_SATA_AHCI_PLATFORM
./scripts/config --enable CONFIG_SATA_PMP           # CFL enables this, CRO explicitly marks it unset
./scripts/config --enable CONFIG_SCSI
./scripts/config --enable CONFIG_SCSI_COMMON
./scripts/config --enable CONFIG_SCSI_CONSTANTS
./scripts/config --enable CONFIG_SCSI_DMA
./scripts/config --enable CONFIG_SCSI_LOGGING
./scripts/config --enable CONFIG_SCSI_MOD
./scripts/config --enable CONFIG_SCSI_SCAN_ASYNC
./scripts/config --module CONFIG_SCSI_VIRTIO       # CFL uses 'm', CRO uses 'y'

# RAID/Device Mapper/Virtual Block
./scripts/config --module CONFIG_BCACHE
./scripts/config --module CONFIG_BLK_DEV_FD
./scripts/config --module CONFIG_BLK_DEV_LOOP
./scripts/config --module CONFIG_BLK_DEV_NBD
./scripts/config --module CONFIG_BLK_DEV_NVME
./scripts/config --module CONFIG_BLK_DEV_PCIESSD_MTIP32XX
./scripts/config --module CONFIG_BLK_DEV_RAM
./scripts/config --module CONFIG_BLK_DEV_RBD
./scripts/config --module CONFIG_BLK_DEV_RNBD_CLIENT
./scripts/config --module CONFIG_BLK_DEV_RNBD_SERVER
./scripts/config --module CONFIG_BLK_DEV_UBLK
./scripts/config --module CONFIG_BLK_DEV_ZONED_LOOP
./scripts/config --module CONFIG_CDROM_PKTCDVD
./scripts/config --module CONFIG_DM_CACHE
./scripts/config --enable CONFIG_DM_BUFIO
./scripts/config --module CONFIG_DM_CRYPT
./scripts/config --module CONFIG_DM_INTEGRITY
./scripts/config --enable CONFIG_DM_MIRROR
./scripts/config --module CONFIG_DM_MULTIPATH
./scripts/config --module CONFIG_DM_RAID
./scripts/config --enable CONFIG_DM_SNAPSHOT
./scripts/config --module CONFIG_DM_THIN_PROVISIONING
./scripts/config --module CONFIG_DM_VERITY
./scripts/config --module CONFIG_DM_WRITECACHE
./scripts/config --enable CONFIG_DM_ZERO
./scripts/config --module CONFIG_MD_LINEAR
./scripts/config --module CONFIG_MD_RAID0
./scripts/config --module CONFIG_MD_RAID1
./scripts/config --module CONFIG_MD_RAID10
./scripts/config --module CONFIG_MD_RAID456
./scripts/config --module CONFIG_NVME_CORE
./scripts/config --module CONFIG_NVME_FABRICS
./scripts/config --module CONFIG_NVME_FC
./scripts/config --module CONFIG_NVME_RDMA
./scripts/config --module CONFIG_NVME_TARGET
./scripts/config --module CONFIG_NVME_TCP
./scripts/config --enable CONFIG_VIRTIO_BLK        # CFL uses 'y', CRO uses 'm'
./scripts/config --module CONFIG_VMD               # CFL uses 'm', CRO uses 'y'
./scripts/config --module CONFIG_XEN_BLKDEV_BACKEND
./scripts/config --module CONFIG_XEN_BLKDEV_FRONTEND
./scripts/config --module CONFIG_ZRAM

# Partition Types
./scripts/config --enable CONFIG_AIX_PARTITION
./scripts/config --enable CONFIG_BSD_DISKLABEL
./scripts/config --enable CONFIG_EFI_PARTITION
./scripts/config --enable CONFIG_LDM_PARTITION
./scripts/config --enable CONFIG_MAC_PARTITION
./scripts/config --enable CONFIG_MINIX_SUBPARTITION
./scripts/config --enable CONFIG_MSDOS_PARTITION
./scripts/config --enable CONFIG_OSF_PARTITION
./scripts/config --enable CONFIG_SGI_PARTITION
./scripts/config --enable CONFIG_SOLARIS_X86_PARTITION
./scripts/config --enable CONFIG_SUN_PARTITION
./scripts/config --enable CONFIG_UNIXWARE_DISKLABEL

# File Systems
./scripts/config --enable CONFIG_BTRFS_FS
./scripts/config --module CONFIG_EROFS_FS
./scripts/config --module CONFIG_EXFAT_FS
./scripts/config --enable CONFIG_EXT4_FS
./scripts/config --module CONFIG_F2FS_FS
./scripts/config --module CONFIG_FAT_FS
./scripts/config --module CONFIG_ISO9660_FS
./scripts/config --module CONFIG_MINIX_FS
./scripts/config --module CONFIG_MSDOS_FS
./scripts/config --module CONFIG_NTFS3_FS
./scripts/config --module CONFIG_ROMFS_FS
./scripts/config --module CONFIG_SQUASHFS
./scripts/config --module CONFIG_UDF_FS
./scripts/config --module CONFIG_VFAT_FS

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
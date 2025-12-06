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
./scripts/config --enable CONFIG_EFI_PARTITION
./scripts/config --enable CONFIG_MSDOS_PARTITION

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

# Core Kernel and General Setup
./scripts/config --enable CONFIG_SYSVIPC           # Fedora setting: y [1]
./scripts/config --enable CONFIG_POSIX_MQUEUE      # Fedora setting: y [1]
./scripts/config --enable CONFIG_AUDIT             # Fedora setting: y [1]
./scripts/config --enable CONFIG_AUDITSYSCALL      # Fedora setting: y [1]
./scripts/config --module CONFIG_IKHEADERS         # Fedora setting: m [2]
./scripts/config --enable CONFIG_FUTEX_PI          # Fedora setting: y [3]
./scripts/config --enable CONFIG_IO_URING          # Fedora setting: y [3]
./scripts/config --enable CONFIG_KEXEC_CORE        # Fedora setting: y [4]
./scripts/config --enable CONFIG_CRASH_DUMP        # Fedora setting: y [4]
./scripts/config --enable CONFIG_RSEQ              # Fedora setting: y [3]

# Scheduling and Resource Management
./scripts/config --enable CONFIG_SCHED_CORE        # Fedora setting: y [5]
./scripts/config --enable CONFIG_VIRT_CPU_ACCOUNTING # Fedora setting: y [5]
./scripts/config --enable CONFIG_CGROUPS           # Fedora setting: y [6]
./scripts/config --enable CONFIG_MEMCG             # Fedora setting: y [6]
./scripts/config --enable CONFIG_CFS_BANDWIDTH     # Fedora setting: y [6]
./scripts/config --enable CONFIG_CPUSETS           # Fedora setting: y [7]
./scripts/config --enable CONFIG_NUMA_BALANCING    # Fedora setting: y [6]
./scripts/config --enable CONFIG_NAMESPACES        # Fedora setting: y [7]
./scripts/config --enable CONFIG_USER_NS           # Fedora setting: y [7]

# CPU and Architecture Features
./scripts/config --enable CONFIG_HPET_TIMER        # Fedora setting: y [8]
./scripts/config --enable CONFIG_X86_MCE           # Fedora setting: y [9]
./scripts/config --enable CONFIG_NUMA              # Fedora setting: y [10]
./scripts/config --enable CONFIG_X86_UMIP          # Fedora setting: y [11]
./scripts/config --enable CONFIG_X86_CET           # Fedora setting: y [12]
./scripts/config --enable CONFIG_AMD_MEM_ENCRYPT   # Fedora setting: y [10]

# Power Management and Suspend
./scripts/config --enable CONFIG_SUSPEND           # Fedora setting: y [13]
./scripts/config --enable CONFIG_HIBERNATION       # Fedora setting: y [13]
./scripts/config --enable CONFIG_ACPI_BATTERY      # Fedora setting: y [14]
./scripts/config --enable CONFIG_CPU_FREQ          # Fedora setting: y [15]
./scripts/config --enable CONFIG_CPU_IDLE          # Fedora setting: y [16]
./scripts/config --enable CONFIG_INTEL_IDLE        # Fedora setting: y [17] (Note: ChromeOS [18] sets this to 'y', but listing for completion if it was missing or different.)

# Networking and Filtering
./scripts/config --enable CONFIG_NET_INGRESS       # Fedora setting: y [19]
./scripts/config --enable CONFIG_NET_EGRESS        # Fedora setting: y [19]
./scripts/config --enable CONFIG_NETFILTER_ADVANCED # Fedora setting: y [20]
./scripts/config --module CONFIG_NF_CONNTRACK      # Fedora setting: m [21]
./scripts/config --enable CONFIG_MPTCP             # Fedora setting: y [20]

# Virtualization
./scripts/config --enable CONFIG_VIRTUALIZATION    # Fedora setting: y [22]
./scripts/config --enable CONFIG_KVM_COMMON        # Fedora setting: y [23]
./scripts/config --enable CONFIG_XEN_DOM0          # Fedora setting: y [24]

# General Driver Infrastructure and Peripherals
./scripts/config --enable CONFIG_INPUT             # Fedora setting: y [25]
./scripts/config --enable CONFIG_INPUT_KEYBOARD    # Fedora setting: y [25]
./scripts/config --enable CONFIG_INPUT_MOUSE       # Fedora setting: y [26]
./scripts/config --enable CONFIG_FW_LOADER         # Fedora setting: y [27]
./scripts/config --enable CONFIG_USB_SUPPORT       # Fedora setting: y (Implied by USB subsystem configs)
./scripts/config --enable CONFIG_USB_XHCI_HCD      # Fedora setting: y [28]
./scripts/config --enable CONFIG_USB_EHCI_HCD      # Fedora setting: y [28]

# Core MMC Infrastructure
./scripts/config --module CONFIG_MMC                 # Fedora setting: m [2]
./scripts/config --module CONFIG_MMC_BLOCK           # Fedora setting: m [2]
./scripts/config --module CONFIG_SDIO_UART           # Fedora setting: m [2]
./scripts/config --set-val CONFIG_MMC_BLOCK_MINORS 8 # Fedora setting: 8 [2]

# Standard SDHCI and Host Controllers
./scripts/config --module CONFIG_MMC_SDHCI           # Fedora setting: m [3]
./scripts/config --enable CONFIG_MMC_SDHCI_IO_ACCESSORS # Fedora setting: y [3]
./scripts/config --module CONFIG_MMC_SDHCI_UHS2      # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_SDHCI_PCI       # Fedora setting: m [3]
./scripts/config --enable CONFIG_MMC_RICOH_MMC       # Fedora setting: y [3]
./scripts/config --module CONFIG_MMC_SDHCI_ACPI      # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_SDHCI_PLTFM     # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_WBSD            # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_ALCOR           # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_TIFM_SD         # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_SDRICOH_CS      # Fedora setting: m [3]
./scripts/config --module CONFIG_MMC_REALTEK_USB     # Fedora setting: m [4]
./scripts/config --module CONFIG_MMC_CQHCI           # Fedora setting: m [4]
./scripts/config --module CONFIG_MMC_HSQ             # Fedora setting: m [4]
./scripts/config --module CONFIG_MMC_TOSHIBA_PCI     # Fedora setting: m [4]
./scripts/config --module CONFIG_MMC_SDHCI_XENON     # Fedora setting: m [4]

# Power Management & ACPI
./scripts/config --module CONFIG_ACPI
./scripts/config --module CONFIG_BATTERY
./scripts/config --module CONFIG_CHARGER
./scripts/config --module CONFIG_POWER_RESET
./scripts/config --module CONFIG_REGULATOR
./scripts/config --module CONFIG_PWM

# Graphics & Display (DRM)
./scripts/config --module CONFIG_DRM
./scripts/config --module CONFIG_DRM_AMD_DC
./scripts/config --module CONFIG_DRM_NOUVEAU
./scripts/config --module CONFIG_DRM_I915
./scripts/config --module CONFIG_DRM_RADEON
./scripts/config --module CONFIG_FRAMEBUFFER_CONSOLE
./scripts/config --module CONFIG_BACKLIGHT_CLASS_DEVICE
./scripts/config --module CONFIG_VIDEO_DEV
./scripts/config --module CONFIG_CEC_CORE

# Networking (Wireless & Wired)
./scripts/config --module CONFIG_NET
./scripts/config --module CONFIG_INET
./scripts/config --module CONFIG_CFG80211
./scripts/config --module CONFIG_MAC80211
./scripts/config --module CONFIG_BT
./scripts/config --module CONFIG_NFC
./scripts/config --module CONFIG_IWLWIFI
./scripts/config --module CONFIG_ATH_CARDS
./scripts/config --module CONFIG_BRCMFMAC
./scripts/config --module CONFIG_MT76_CORE
./scripts/config --module CONFIG_MWIFIEX

# Input Devices (Touch/Keyboard)
./scripts/config --module CONFIG_INPUT
./scripts/config --module CONFIG_HID
./scripts/config --module CONFIG_KEYBOARD_ATKBD
./scripts/config --module CONFIG_MOUSE_PS2
./scripts/config --module CONFIG_TOUCHSCREEN_ELAN
./scripts/config --module CONFIG_RMI4_CORE

# Connectivity & Buses
./scripts/config --module CONFIG_USB
./scripts/config --module CONFIG_TYPEC
./scripts/config --module CONFIG_THUNDERBOLT
./scripts/config --module CONFIG_I2C
./scripts/config --module CONFIG_SPI
./scripts/config --module CONFIG_GPIO_CDEV

# Storage & Crypto
./scripts/config --module CONFIG_NVME_CORE
./scripts/config --module CONFIG_MMC
./scripts/config --module CONFIG_CRYPTO

# ComposeFS required for Fedora atomic
./scripts/config --enable CONFIG_OVERLAY_FS
./scripts/config --enable CONFIG_BLK_DEV_LOOP
./scripts/config --enable CONFIG_EROFS_FS

# 1. Enable EROFS & Compression (Required to read the image data)
./scripts/config --enable CONFIG_EROFS_FS
./scripts/config --enable CONFIG_EROFS_FS_ZIP
./scripts/config --enable CONFIG_EROFS_FS_ZIP_LZ4
./scripts/config --enable CONFIG_EROFS_FS_ZIP_ZSTD

# 2. Enable OverlayFS (Required to layer the image)
./scripts/config --enable CONFIG_OVERLAY_FS
./scripts/config --enable CONFIG_OVERLAY_FS_REDIRECT_DIR
./scripts/config --enable CONFIG_OVERLAY_FS_REDIRECT_ALWAYS_FOLLOW

# 3. Enable FS_Verity (REQUIRED for ComposeFS to mount at all)
./scripts/config --enable CONFIG_FS_VERITY

# 4. DISABLE Built-in Signatures (CRITICAL: Fixes the boot loop)
# If this is 'y', the kernel rejects the Fedora image because it isn't signed by YOU.
./scripts/config --disable CONFIG_FS_VERITY_BUILTIN_SIGNATURES

# [FIX] Force Autofs to be built-in to satisfy systemd
./scripts/config --enable CONFIG_AUTOFS_FS

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
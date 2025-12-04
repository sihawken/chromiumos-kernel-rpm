.PHONY: srpm

# 1. Define the Fedora release for config files (e.g., f41, f43, rawhide)
FEDORA_RELEASE=f43

srpm:
	# --- Install Dependencies ---
	dnf install -y fedpkg fedora-packager rpmdevtools git tar sed

	# --- Fetch Chromium Source ---
	# Clone into a temporary folder
	git clone --depth 1 https://chromium.googlesource.com/chromiumos/third_party/kernel linux-chromium

	# --- Detect Version from Source ---
	# Extract version components from the Chromium Makefile (e.g., 6, 12, 5)
	$(eval K_MAJOR := $(shell grep -m1 "^VERSION =" linux-chromium/Makefile | cut -d= -f2 | tr -d ' '))
	$(eval K_PATCH := $(shell grep -m1 "^PATCHLEVEL =" linux-chromium/Makefile | cut -d= -f2 | tr -d ' '))
	$(eval K_SUB   := $(shell grep -m1 "^SUBLEVEL =" linux-chromium/Makefile | cut -d= -f2 | tr -d ' '))
	$(eval K_VER   := $(K_MAJOR).$(K_PATCH).$(K_SUB))

	@echo "------------------------------------------------"
	@echo "Detected Chromium Kernel Version: $(K_VER)"
	@echo "------------------------------------------------"

	# --- Prepare Build Environment ---
	# Clone Fedora kernel repo to get the aux files (generate_all_configs.sh, etc)
	git clone https://src.fedoraproject.org/rpms/kernel.git build-env
	cd build-env && git checkout $(FEDORA_RELEASE)

	# --- Update Spec File ---
	# Copy YOUR uploaded spec file into the build environment
	cp kernel.spec build-env/

	# Dynamically update the version macros in the spec file to match the source
	# We strictly replace the existing %define lines
	sed -i 's/%define specrpmversion .*/%define specrpmversion $(K_VER)/' build-env/kernel.spec
	sed -i 's/%define specversion .*/%define specversion $(K_VER)/' build-env/kernel.spec
	sed -i 's/%define patchversion .*/%define patchversion $(K_MAJOR).$(K_PATCH)/' build-env/kernel.spec
	sed -i 's/%define kversion .*/%define kversion $(K_MAJOR)/' build-env/kernel.spec
	sed -i 's/%define tarfile_release .*/%define tarfile_release $(K_VER)/' build-env/kernel.spec
	sed -i 's/%define patchlevel .*/%define patchlevel $(K_PATCH)/' build-env/kernel.spec

	# Ensure the Source0 tag points to the tarball we are about to create
	sed -i 's|^Source0:.*|Source0: linux-$(K_VER).tar.xz|' build-env/kernel.spec

	# --- Create Source Tarball ---
	# The spec expects the tarball to unpack into a directory named 'linux-X.Y.Z'
	# We use --transform to rename the top-level directory inside the archive
	tar --exclude-vcs --transform 's,^linux-chromium,linux-$(K_VER),' -cJf build-env/linux-$(K_VER).tar.xz linux-chromium

	# --- Build SRPM ---
	# We define 'buildid' here to append a custom tag (e.g., kernel-6.12.5-300.chromium.fc41)
	cd build-env && rpmbuild \
		--define "_sourcedir $(PWD)/build-env" \
		--define "_specdir $(PWD)/build-env" \
		--define "_srcrpmdir $(PWD)" \
		--define "buildid .chromium" \
		-bs kernel.spec

	# --- Output ---
	mv *.src.rpm .
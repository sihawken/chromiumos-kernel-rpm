# variables
FEDORA_RELEASE=f43 # Change this to f40, rawhide, etc. as needed

srpm:
	# 1. Install Tooling
	dnf install -y fedpkg fedora-packager rpmdevtools git tar sed

	# 2. Clone the Official Fedora Packaging
	# We clone into a folder named 'fedora-packaging'
	git clone https://src.fedoraproject.org/rpms/kernel.git fedora-packaging
	cd fedora-packaging && git checkout $(FEDORA_RELEASE)

	# 3. Clone Chromium OS Kernel
	# We clone into 'linux-custom' to match typical extraction expectation
	git clone --depth 1 https://chromium.googlesource.com/chromiumos/third_party/kernel linux-custom

	# 4. Determine Chromium Kernel Version
	# We grab the Makefile version from the Chromium source (e.g., 6.6.0)
	$(eval KVER_MAJOR := $(shell grep -m1 "^VERSION =" linux-custom/Makefile | cut -d= -f2 | tr -d ' '))
	$(eval KVER_PATCH := $(shell grep -m1 "^PATCHLEVEL =" linux-custom/Makefile | cut -d= -f2 | tr -d ' '))
	$(eval KVER_SUB   := $(shell grep -m1 "^SUBLEVEL =" linux-custom/Makefile | cut -d= -f2 | tr -d ' '))
	$(eval KVER := $(KVER_MAJOR).$(KVER_PATCH).$(KVER_SUB))
	
	@echo "Detected Chromium Version: $(KVER)"

	# 5. Create the Tarball
	# The Fedora spec usually expects linux-<version>.tar.xz
	tar --exclude-vcs -cJf fedora-packaging/linux-$(KVER).tar.xz linux-custom

	# 6. Modify the Fedora Spec File
	# We must force the spec to use our version and our tarball
	# sed -i 's/Search/Replace/g' filename
	
	# Update Version
	sed -i 's/^%define base_sublevel.*/%define base_sublevel $(KVER_SUB)/' fedora-packaging/kernel.spec
	
	# disable the "sources" check since we are providing a local tarball
	# We also need to ensure Source0 points to our local file, not a URL
	sed -i 's|^Source0:.*|Source0: linux-$(KVER).tar.xz|' fedora-packaging/kernel.spec

	# 7. NUKE THE PATCHES (CRITICAL STEP)
	# Fedora patches will almost certainly fail to apply to a Chromium kernel.
	# We disable the patch application logic. 
	# This sed command comments out the lines that apply patches.
	sed -i 's/^ApplyOptionalPatch/# ApplyOptionalPatch/' fedora-packaging/kernel.spec
	sed -i 's/^%patch/# %patch/' fedora-packaging/kernel.spec

	# 8. Build the SRPM
	# We use rpmbuild -bs because fedpkg srpm tries to download sources
	cd fedora-packaging && rpmbuild \
		--define "_sourcedir $(PWD)/fedora-packaging" \
		--define "_specdir $(PWD)/fedora-packaging" \
		--define "_srcrpmdir $(PWD)" \
		--define "buildid .chromium" \
		-bs kernel.spec

	# 9. Cleanup
	# Move the generated SRPM to the root so COPR finds it
	mv *.src.rpm .
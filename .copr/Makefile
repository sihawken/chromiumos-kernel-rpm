.PHONY: srpm

# Variables
# We need to know which Fedora branch to clone for the config files
FEDORA_RELEASE=f43

srpm:
	# 1. Install Build Dependencies
	dnf install -y fedpkg fedora-packager rpmdevtools git tar

	# 2. Prepare Build Directory with Fedora Assets
	# We clone the official Fedora kernel repo to get the hundreds of config files
	# and scripts (e.g., generate_all_configs.sh) that the spec depends on.
	git clone https://src.fedoraproject.org/rpms/kernel.git build-env
	cd build-env && git checkout $(FEDORA_RELEASE)

	# 3. Install YOUR Spec File
	# Overwrite the Fedora spec with the one from this repo
	cp kernel.spec build-env/

	# 4. Clone Chromium OS Kernel Source
	# We clone into a temporary directory
	git clone --depth 1 https://chromium.googlesource.com/chromiumos/third_party/kernel linux-chromium

	# 5. Determine Expected Tarball Name from Your Spec
	# We read the 'tarfile_release' definition from your spec (e.g., 6.17.10)
	# This ensures the tarball we create matches exactly what Source0 expects.
	$(eval KVER := $(shell grep "%define tarfile_release" kernel.spec | head -n1 | awk '{print $$3}'))
	
	@echo "Spec file expects version: $(KVER)"
	@echo "Creating tarball: linux-$(KVER).tar.xz"

	# 6. Create the Source Tarball
	# The spec expects the tarball to unpack into a directory named 'linux-6.17.10'
	# We use --transform to rename the top-level directory inside the tarball
	tar --exclude-vcs --transform 's,^linux-chromium,linux-$(KVER),' -cJf build-env/linux-$(KVER).tar.xz linux-chromium

	# 7. Build the SRPM
	# We run rpmbuild inside the build-env directory where specs and sources now live
	cd build-env && rpmbuild \
		--define "_sourcedir $(PWD)/build-env" \
		--define "_specdir $(PWD)/build-env" \
		--define "_srcrpmdir $(PWD)" \
		--define "buildid .chromium" \
		-bs kernel.spec

	# 8. Cleanup
	# COPR expects the SRPM in the root of the repo
	mv *.src.rpm .
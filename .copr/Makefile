srpm:
	dnf install -y git tar
	# Create necessary directories
	mkdir -p rpmbuild/{SOURCES,SPECS}
	
	# Clone the Chromium OS kernel (shallow clone for speed)
	# You can change the branch/tag here if needed (e.g., -b release-R100-...)
	git clone --depth 1 https://chromium.googlesource.com/chromiumos/third_party/kernel chromium-kernel
	
	# Create the tarball expected by the spec file
	tar --exclude-vcs -cJf rpmbuild/SOURCES/linux-chromiumos.tar.xz chromium-kernel
	
	# Copy the spec file to the build directory
	cp kernel-chromiumos.spec rpmbuild/SPECS/
	
	# Build the SRPM
	rpmbuild \
		--define "_topdir $$(pwd)/rpmbuild" \
		--define "_sourcedir $$(pwd)/rpmbuild/SOURCES" \
		--define "_specdir $$(pwd)/rpmbuild/SPECS" \
		--define "_srcrpmdir $(outdir)" \
		-bs rpmbuild/SPECS/kernel-chromiumos.spec
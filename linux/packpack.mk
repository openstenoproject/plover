PACKAGE := $(PRODUCT)-$(VERSION)

.PHONY: appimage

appimage:
	tar xf dist/$(PACKAGE).tar.xz -C /build
	cd /build/$(PACKAGE) && \
		ln -s /cache .cache && \
		env MAKEFLAGS='' ./linux/appimage/build.sh -w /source/dist/$(PACKAGE)-py3-none-any.whl -c -j 2 && \
		mv dist/*.AppImage ..

.PHONY: makepkg

makepkg:
	sed 's,^pkgver=.*,pkgver=$(VERSION),;s,^source=.*,source=($(PACKAGE).tar.xz),' archlinux/PKGBUILD >/build/PKGBUILD
	cd /build && makepkg --noconfirm --syncdeps --rmdeps --skipchecksums --force

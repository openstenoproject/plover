PACKAGE := $(PRODUCT)-$(VERSION)

.PHONY: appimage

appimage:
	tar xf dist/$(PACKAGE).tar.xz -C /build
	cd /build/$(PACKAGE) && \
		ln -s /cache .cache && \
		env MAKEFLAGS='' ./linux/appimage/build.sh -w /source/dist/$(PACKAGE)-py2.py3-none-any.whl -c -j 2 && \
		mv dist/*.AppImage ..

.PHONY: makepkg

makepkg:
	mkdir -p /build/src
	tar xf dist/$(PACKAGE).tar.xz -C /build/src
	sed 's,^pkgver=.*,pkgver=$(VERSION),' archlinux/PKGBUILD >/build/PKGBUILD
	cd /build && makepkg --force --syncdeps --noconfirm --noextract

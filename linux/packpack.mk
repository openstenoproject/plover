PACKAGE := $(PRODUCT)-$(VERSION)

.PHONY: appimage

appimage:
	tar xf /build/$(PACKAGE).tar.xz -C /build
	cd /build/$(PACKAGE) && \
		ln -s /cache .cache && \
		python3 setup.py bdist_appimage && \
		mv dist/*.AppImage ..

.PHONY: makepkg

makepkg:
	sed 's,^pkgver=.*,pkgver=$(VERSION),;s,^source=.*,source=($(PACKAGE).tar.xz),' archlinux/PKGBUILD >/build/PKGBUILD
	cd /build && makepkg --noconfirm --syncdeps --rmdeps --skipchecksums --force

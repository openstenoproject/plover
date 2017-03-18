PACKAGE := $(PRODUCT)-$(VERSION)

.PHONY: appimage

appimage:
	tar xf dist/$(PACKAGE).tar.xz -C /build
	cd /build/$(PACKAGE) && \
		ln -s /cache .cache && \
		env MAKEFLAGS='' ./linux/appimage.sh -w /source/dist/$(PACKAGE)-py2.py3-none-any.whl -c -j 2 && \
		mv dist/*.AppImage ..

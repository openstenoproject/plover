# Set PYTHON to the version to be deployed. This may or may not be the default
# installation.
PYTHON ?= python

all: Plover.dmg

dist/Plover.app:
	$(PYTHON) setup.py py2app
	rm ../launch.py
	ditto --arch i386 dist/Plover.app dist/PloverStripped.app
	rm -rf dist/Plover.app
	mv dist/PloverStripped.app dist/Plover.app

Plover.dmg: dist/Plover.app
	mkdir tmp
	cp plover_template.dmg.gz tmp/plover_template.dmg.gz
	gunzip tmp/plover_template.dmg.gz 
	hdiutil resize -size 100m tmp/plover_template.dmg 
	mkdir tmp/plover_mountpoint
	hdiutil attach tmp/plover_template.dmg -noautoopen -quiet -mountpoint tmp/plover_mountpoint
	rm -rf tmp/plover_mountpoint/Plover.app
	ditto dist/Plover.app tmp/plover_mountpoint/Plover.app
	hdiutil detach $$(hdiutil info | grep plover_mountpoint | grep Apple_HFS | cut -f1)
	rmdir tmp/plover_mountpoint
	hdiutil convert tmp/plover_template.dmg -format UDZO -imagekey zlib-level=9 -o Plover.dmg
	rm tmp/plover_template.dmg
	rmdir tmp

.PHONY: clean
clean:
	-rm -rf build/ dist/ Plover.dmg tmp/

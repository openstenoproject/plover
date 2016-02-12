# Set PYTHON to the version to be deployed. This may or may not be the default
# installation.
PYTHON ?= python

topdir = ..
builddir = $(topdir)/build
distdir = $(topdir)/dist

APP = $(distdir)/Plover.app
DMG = $(distdir)/Plover.dmg

.PHONY: all app dmg clean

all: dmg

app: $(APP)
dmg: $(DMG)

$(APP):
	cd $(topdir) && $(PYTHON) setup.py py2app
	ditto --arch x86_64 $(APP) $(APP:%.app=%Stripped.app)
	rm -rf $(APP)
	mv $(APP:%.app=%Stripped.app) $(APP)

$(DMG): $(APP)
	mkdir tmp
	cp plover_template.dmg.gz tmp/plover_template.dmg.gz
	gunzip tmp/plover_template.dmg.gz 
	hdiutil resize -size 100m tmp/plover_template.dmg 
	mkdir tmp/plover_mountpoint
	hdiutil attach tmp/plover_template.dmg -noautoopen -quiet -mountpoint tmp/plover_mountpoint
	rm -rf tmp/plover_mountpoint/Plover.app
	ditto $(APP) tmp/plover_mountpoint/Plover.app
	hdiutil detach $$(hdiutil info | grep plover_mountpoint | grep Apple_HFS | cut -f1)
	rmdir tmp/plover_mountpoint
	hdiutil convert tmp/plover_template.dmg -format UDZO -imagekey zlib-level=9 -o $(DMG)
	rm tmp/plover_template.dmg
	rmdir tmp

clean:
	-rm -rf $(builddir) $(distdir) $(APP) $(DMG) tmp/

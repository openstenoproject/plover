# -*- mode: python -*-
#
# To build the package for windows:
# - Make sure all dependencies are installed.
# - Get pyInstaller and put it where you like. Let's call the location PYINSTALLPATH.
# - Run: python -O application\plover to make sure all the .pyo files are generated.
# - Run: python -O PYINSTALLPATH\Configure.py
# - Run: python -O PYINSTALLPATH\Build.py pyinstaller.spec

a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'application\plover'],
             pathex=['C:\\Documents and Settings\\Rachel Rivera\\Desktop\\hesky\\plover\\plover'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts + [('O','','OPTION')],
          a.binaries,
          a.zipfiles,
          a.datas,
          Tree('plover\\assets'),
          name=os.path.join('dist', 'plover.exe'),
          debug=False,
          strip=False,
          upx=False,
          console=False,
          icon='plover\\assets\\plover.ico' )
app = BUNDLE(exe,
             name=os.path.join('dist', 'plover.exe.app'))

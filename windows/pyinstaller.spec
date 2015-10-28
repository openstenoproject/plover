# -*- mode: python -*-
a = Analysis(['..\\launch.py'],
             pathex=['..'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          Tree('..\\plover\\assets'),
          name=os.path.join('dist', 'plover.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='plover.ico')

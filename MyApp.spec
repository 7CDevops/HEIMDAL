# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew

block_cipher = None


a = Analysis(['MyApp.py'],
             pathex=[],
             binaries=[],
             datas=[('MyApp.kv', '.')],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a.datas += [(r'Images\fond.jpg',r'C:\Users\a.colas\PycharmProjects\heimdal\Images\fond.jpg', "DATA")]
a.datas += [(r'Images\noir.ico',r'C:\Users\a.colas\PycharmProjects\heimdal\Images\noir.ico', "DATA")]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='Heimdall',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon=r'C:\Users\a.colas\PycharmProjects\heimdal\Images\noir.ico' )

# pyinstaller.exe --onefile .\MyApp.spec
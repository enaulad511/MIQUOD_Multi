# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe for the MIQUOD desktop application: a single windowed dist\MIQUOD.exe.
#
# Build from this folder, with the virtual environment that has requirements-build.txt:
#
#     ..\.venv\Scripts\python -m PyInstaller --noconfirm miquod_gui.spec
#
# Everything the bundle needs is found by following the imports of miquod_gui.py; the application
# loads no data files of its own, so there is nothing to list under datas.

a = Analysis(['miquod_gui.py'])
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='MIQUOD',
    console=False,  # no terminal window behind the application
    upx=False,      # UPX can break the OpenCV and numpy DLLs and makes antivirus false positives likelier
)

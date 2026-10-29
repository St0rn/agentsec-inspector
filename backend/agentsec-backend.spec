# -*- mode: python ; coding: utf-8 -*-
datas = [("agentsec/templates", "agentsec/templates"), ("migrations", "migrations")]
binaries = []
hiddenimports = []

a = Analysis(["standalone.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hiddenimports, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="agentsec-backend", debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)

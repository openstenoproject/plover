@pushd %~dp0
python -m compileall ..
pyinstaller pyinstaller.spec
@popd

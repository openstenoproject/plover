@pushd %~dp0
python.exe setup.py launch -- %*
@popd

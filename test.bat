@pushd %~dp0
python.exe setup.py test -- %*
@popd

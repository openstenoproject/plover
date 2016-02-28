@pushd %~dp0
powershell wget https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi -OutFile python.msi
msiexec /i python.msi
C:\Python27\python.exe helper.py setup -i
@popd
@pause Press a key to close this window.

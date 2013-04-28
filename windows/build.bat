@IF "%~1"=="" GOTO Error
@set pyinstaller="%~f1"
@pushd %~dp0
python -m compileall ..
@rem %1 should be the path to pyinstaller-2.0
python %pyinstaller%\pyinstaller.py pyinstaller.spec
@popd
@GOTO:EOF
:Error
@ECHO First argument should be the path to pyinstaller-2.0
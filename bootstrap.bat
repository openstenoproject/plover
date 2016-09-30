@pushd %~dp0
@powershell "& { Start-Process PowerShell.exe -Wait -Verb RunAs -ArgumentList 'cd %~dp0\windows; . .\bootstrap.ps1; pause' }"

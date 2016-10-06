pushd ${PSScriptRoot}
try
{
     $installer="py3setup.exe"
     if (!(Test-Path $installer))
     {
         write-host "downloading Python"
         wget https://www.python.org/ftp/python/3.5.2/python-3.5.2.exe -OutFile $installer
     }
     $sha1=$($(CertUtil -hashfile $installer SHA1 | findstr /vb /c:SHA1 /c:CertUtil) -replace " ","")
     if ($sha1 -ne "3873deb137833a724be8932e3ce659f93741c20b")
     {
         write-host "Python installer SHA1 does not match!"
         rm $installer
         break
     }
     write-host "installing Python"
     & .\\$installer PrependPath=1 Include_tcltk=0 | Wait-Process
     # Refresh PATH.
     $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
     & python.exe helper.py -v setup -i
}
finally
{
    popd
}

# vim: ft=sh sw=4

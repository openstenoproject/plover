pushd ${PSScriptRoot}
try
{
     $installer="py2setup.exe"
     if (!(Test-Path $installer))
     {
         write-host "downloading Python"
         wget https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi -OutFile $installer
     }
     $sha1=$($(CertUtil -hashfile $installer SHA1 | findstr /vb /c:SHA1 /c:CertUtil) -replace " ","")
     if ($sha1 -ne "662142691e0beba07a0bacee48e5e93a02537ff7")
     {
         write-host "Python installer SHA1 does not match!"
         rm $installer
         break
     }
     write-host "installing Python"
     & .\\$installer | Wait-Process
     # Refresh PATH.
     $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
     & python.exe helper.py -v setup -i
}
finally
{
    popd
}

# vim: ft=sh sw=4

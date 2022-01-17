# Windows Development

## Environment setup

Some of the development helpers rely on `bash` being available. You can use the
version provided by the official `git` installer.

For the quickest way to get started developing in Windows, use WinPython, *not*
Anaconda/Miniconda. Some users report impossible dependency/build headaches when
initializing a development environment starting from a base Miniconda3
installation that is otherwise working perfectly.

You will also need Microsoft Build Tools and an SDK appropriate for your
operating system. These are required in order to build the `plover-stroke`
package, which contains C code and does not currently have cross-platform Python
wheel packages available. These two tools can be downloaded from their official
sources here:

- https://winpython.github.io/
- https://visualstudio.microsoft.com/visual-cpp-build-tools/

**NOTE 1:** You can choose whichever WinPython release you want (32-bit/64-bit),
including the smallest "dot" releases that contain only the bare minimum
required for a functional Python interpreter. If you choose this or any other
pre-built installer that does not include the `tox` package, you will need to
install it with `pip` later.

**NOTE 2:** There seem to be many sources for various MS Build Tools installers,
even from Microsoft. The above link is the correct one as of early 2022. When
you run the installer, make sure you select **both** the SDK for your Windows
version and the build tools for it. As of early 2022, you should choose
**"Windows 10 SDK (10.0.19041.0)"** and **"MSVC v142 - VS 2019 C++ x64/x86 build
tools (Latest)"**, assuming you are running Windows 10. This unfortunately
requires many gigabytes of data for a task that only needs perhaps 20 MB of
binary utilities and header files, but such is life.

Once you have installed WinPython, the MS Build Tools, and the Windows SDK,
browse to your WinPython installation folder (e.g. `C:\Python\WPy32-3980`) and
run the "WinPython Command Prompt" shortcut. You should be able to confirm a
working environment by typing `python -V` and seeing the expected version
displayed. If you haven't already, install `tox` using by typing
`python -m pip install tox`. Finally, run the following to make sure the MS
Build Tools have been made available in your PATH for the development session:

```
"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars32.bat"
```

*(This path may change in the future with new versions of the SDK)*

At this point, you can navigate to the `/openstenoproject/plover` folder where
you have cloned this project and try running the application from source using
the command `tox -e launch`. It will take a while the first time as it
downloads, builds, and installs everything, but you should be greeted with
Plover's main UI window after the initial build completes.

This giant set of hoops for MS Build Tools support *should* only be necessary
the first time you run Plover and get all of its dependencies installed, since
`plover-stroke` will not need to be rebuilt every time (unless, of course, you
are modifying the `plover-stroke` source).

Finally, breathe a sigh of relief and start doing the *real* development work.

See the [developer guide](../doc/developer_guide.md) for the rest of the steps.

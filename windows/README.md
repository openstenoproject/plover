# Windows Development

## Environment setup

Some of the development helpers rely on `bash` being available. You can use the
version provided by the official `git` installer.

For the quickest way to get started developing in Windows, use WinPython, *not*
Anaconda/Miniconda. Some users report impossible dependency/build headaches when
initializing a development environment starting from a base Miniconda3
installation that is otherwise working. WinPython is available here:

- https://winpython.github.io/

Make sure that you select a **64-bit** WinPython release that is >= 3.6. The
smallest available package is fine (the "dot" version with only the bare minimum
required to run Python) since `tox` handles dependencies. However, you will need
to install `tox` using `pip` once before proceeding.

**NOTE**: If you are intending to develop specifically inside the `plover-stroke`
module, you will also need Microsoft Build Tools and an SDK appropriate for your
operating system. This is because the `plover-stroke` module contains C code
rather than just native Python code. **Most people will not need to do this.**
The Microsoft Build Tools installer is available here:

- https://visualstudio.microsoft.com/visual-cpp-build-tools/

When you run the installer, make sure you select **both** the SDK for your
Windows version and the build tools for it (e.g. Windows 10 SDK, MSVC v142).
You will also need to run the appropriate `vcvars64.bat` file from the build
tools installation inside of your Python environment to establish the correct
paths, which is found in a subfolder of `\Program Files (x86)\Microsoft Visual Studio\`.

See the [developer guide](../doc/developer_guide.md) for the rest of the steps.

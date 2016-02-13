# Plover Development on OS X

## Getting Started
- Run `./bootstrap.sh`.
- Run `make app` to produce `../dist/Plover.app`.
  - If you want a disk image instead, use: `make dmg`
  - Standard development practice is to use `make clean app` to produce
    a clean rebuild of the app.


## Gotcha: Granting Assistive Device Permission
After each build, you need to approve Plover as an Assistive Device:

- Open System Preferences
- Open the Security & Privacy pane
- Select the Privacy tab
- Select "Accessibility" from the source list on the left
- Click the "+" button below the list off apps
- Use the file picker to select the Plover.app that you just built

Now you can run the app by double-clicking on it
or by using open(1):

    open ../dist/Plover.app

### Dev Workaround: Run as Root
Root doesn't need permission to use event taps,
so during development, you can avoid this rigmarole by running Plover via:

```
sudo python launch.py
```


## Dependencies
The bootstrap script takes care of these for you, but in case you're curious:

- Python2.7: `brew install python --framework`
- wxPython: `brew install wxpython`
- Various Python libraries, for which see
  [requirements.txt](./requirements.txt).


### Xcode Tools
You need the Xcode command-line tools.
The bootstrap script will walk you through this.

If you want to check for yourself, try running `clang` in Terminal.app.
You will receive a prompt if the tools are not installed
with instructions for how to install them.

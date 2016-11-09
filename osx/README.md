# OS X Development

## Semi-automatic development environment setup

With Homebrew installed, you should be able to have everything setup automatically by using: `./bootstrap.sh`.

Note: you can use `./bootstrap.sh -n` to get a list of the commands that would be run.

## Manual development environment setup

- install [Homebrew](http://brew.sh/)
- install Python2.7: `brew install python`
- install wxPython: `brew install wxpython`
- install other dependencies:
```
./setup.py write_requirements
pip2 install -r requirements.txt -c requirements_constraints.txt
```

## Running Plover in development

To run from source, from the root of the Git repository, use `./launch.sh`.

## Building

- to build to an application, use: `./setup.py bdist_app`
- to create a disk image instead, use: `./setup.py bdist_dmg`

## Gotcha: Granting Assistive Device Permission

After each build, you need to approve Plover as an Assistive Device:

- open "System Preferences"
- open the "Security & Privacy" pane
- select the "Privacy" tab
- select "Accessibility" from the source list on the left
- click the "+" button below the list off apps
- use the file picker to select the `plover.app` that you just built

Now you can run the app by double-clicking on it or by using open(1):

`open dist/plover.app`

### Dev Workaround: run as `root`

Root doesn't need permission to use event taps, so during development, you can avoid this rigmarole by running Plover via:

`sudo ./launch.sh`

**Warning**: running things as root is never a good idea from a security standpoint!

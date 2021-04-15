# Mac Development

## Environment setup

See the [developer guide](../doc/developer_guide.md).


## Gotcha: Assistive Devices Permissions

To grab user inputs and use the keyboard as a steno machine, Plover requires
[Assistive Devices permissions to be granted (instructions
included).](https://support.apple.com/kb/ph18391?locale=en_US)

When running from source, your terminal application must be granted Assistive
Devices permissions.

If you are running from an application bundle (both in development and for
releases), every new build will require re-granting the permissions.

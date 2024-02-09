# Mac Development

## Environment setup

See the [developer guide](../doc/developer_guide.md).


## Gotcha: Accessibility Permissions

To grab user inputs and use the keyboard as a steno machine, Plover requires
[accessibility permissions to be granted (instructions
included).](https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac)

When running from source, your terminal application must be granted
accessibility permissions.

If you are running from an application bundle (both in development and for
releases), every new build will require re-granting the permissions.

# “Microsoft Corp”.
MICROSOFT_VID = 0x045e


def patch_ports_info(port_list):
    '''Patch serial ports info to remove erroneous manufacturer.

    Because on Windows 10 most USB serial devices will use the generic
    CDC/ACM driver, their manufacturer is reported as Microsoft. Strip
    that information if the vendor ID does not match.
    '''
    for port_info in port_list:
        if port_info.manufacturer == 'Microsoft' \
           and port_info.vid != MICROSOFT_VID:
            port_info.manufacturer = None
    return port_list

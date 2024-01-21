from pathlib import Path


def patch_ports_info(port_list):
    '''Patch serial ports info to use device-by-id links.'''
    try:
        device_by_id = {
            str(device.resolve()): str(device)
            for device in Path('/dev/serial/by-id').iterdir()
        }
    except FileNotFoundError:
        device_by_id = {}
    for port_info in port_list:
        port_info.device = device_by_id.get(port_info.device, port_info.device)
    return port_list

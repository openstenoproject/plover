from serial.tools.list_ports import comports as serial_comports

try:
    from plover.oslayer.list_ports_posix import comports as alternative_comports
except ImportError:
    alternative_comports = lambda: []
    
def comports():
    try:
        return serial_comports()
    except NameError:
        # For some reason, the official release of pyserial 2.6 has a simple NameError in it :(
        return alternative_comports()

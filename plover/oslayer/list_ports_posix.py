""" This file is taken from the pyserial source trunk and is licensed as follows:

Copyright (C) 2001-2011 Chris Liechti <cliechti(at)gmx.net>; All Rights Reserved.

This is the Python license. In short, you can use this product in commercial and non-commercial applications, modify it, redistribute it. A notification to the author when you use and/or modify it is welcome.

TERMS AND CONDITIONS FOR ACCESSING OR OTHERWISE USING THIS SOFTWARE

LICENSE AGREEMENT

This LICENSE AGREEMENT is between the copyright holder of this product, and the Individual or Organization ("Licensee") accessing and otherwise using this product 
in source or binary form and its associated documentation.
Subject to the terms and conditions of this License Agreement, the copyright holder hereby grants Licensee a nonexclusive, royalty-free, world-wide license to 
reproduce, analyze, test, perform and/or display publicly, prepare derivative works, distribute, and otherwise use this product alone or in any derivative version, 
provided, however, that copyright holders License Agreement and copyright holders notice of copyright are retained in this product alone or in any derivative version 
prepared by Licensee.
In the event Licensee prepares a derivative work that is based on or incorporates this product or any part thereof, and wants to make the derivative work available 
to others as provided herein, then Licensee hereby agrees to include in any such work a brief summary of the changes made to this product.
The copyright holder is making this product available to Licensee on an "AS IS" basis. THE COPYRIGHT HOLDER MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR 
IMPLIED. BY WAY OF EXAMPLE, BUT NOT LIMITATION, THE COPYRIGHT HOLDER MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY 
PARTICULAR PURPOSE OR THAT THE USE OF THIS PRODUCT WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.
THE COPYRIGHT HOLDER SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF THIS PRODUCT FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF 
MODIFYING, DISTRIBUTING, OR OTHERWISE USING THIS PRODUCT, OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
This License Agreement will automatically terminate upon a material breach of its terms and conditions.
Nothing in this License Agreement shall be deemed to create any relationship of agency, partnership, or joint venture between the copyright holder and Licensee. 
This License Agreement does not grant permission to use trademarks or trade names from the copyright holder in a trademark sense to endorse or promote products or 
services of Licensee, or any third party.
By copying, installing or otherwise using this product, Licensee agrees to be bound by the terms and conditions of this License Agreement.

"""

import glob
import sys
import os
import re

try:
    import subprocess
except ImportError:
    def popen(argv):
        try:
            si, so =  os.popen4(' '.join(argv))
            return so.read().strip()
        except:
            raise IOError('lsusb failed')
else:
    def popen(argv):
        try:
            return subprocess.check_output(argv, stderr=subprocess.STDOUT).strip()
        except:
            raise IOError('lsusb failed')


# The comports function is expected to return an iterable that yields tuples of
# 3 strings: port name, human readable description and a hardware ID.
#
# as currently no method is known to get the second two strings easily, they
# are currently just identical to the port name.

# try to detect the OS so that a device can be selected...
plat = sys.platform.lower()

def read_line(filename):
    """help function to read a single line from a file. returns none"""
    try:
        f = open(filename)
        line = f.readline().strip()
        f.close()
        return line
    except IOError:
        return None

def re_group(regexp, text):
    """search for regexp in text, return 1st group on match"""
    if sys.version < '3':
        m = re.search(regexp, text)
    else:
        # text is bytes-like
        m = re.search(regexp, text.decode('ascii', 'replace'))
    if m: return m.group(1)


if   plat[:5] == 'linux':    # Linux (confirmed)
    # try to extract descriptions from sysfs. this was done by experimenting,
    # no guarantee that it works for all devices or in the future...

    def usb_sysfs_hw_string(sysfs_path):
        """given a path to a usb device in sysfs, return a string describing it"""
        bus, dev = os.path.basename(os.path.realpath(sysfs_path)).split('-')
        snr = read_line(sysfs_path+'/serial')
        if snr:
            snr_txt = ' SNR=%s' % (snr,)
        else:
            snr_txt = ''
        return 'USB VID:PID=%s:%s%s' % (
                read_line(sysfs_path+'/idVendor'),
                read_line(sysfs_path+'/idProduct'),
                snr_txt
                )

    def usb_lsusb_string(sysfs_path):
        base = os.path.basename(os.path.realpath(sysfs_path))

        bus, dev = base.split('-')

        try:
            desc = popen(['lsusb', '-v', '-s', '%s:%s' % (bus, dev)])
            # descriptions from device
            iManufacturer = re_group('iManufacturer\s+\w+ (.+)', desc)
            iProduct = re_group('iProduct\s+\w+ (.+)', desc)
            iSerial = re_group('iSerial\s+\w+ (.+)', desc) or ''
            # descriptions from kernel
            idVendor = re_group('idVendor\s+0x\w+ (.+)', desc)
            idProduct = re_group('idProduct\s+0x\w+ (.+)', desc)
            # create descriptions. prefer text from device, fall back to the others
            return '%s %s %s' % (iManufacturer or idVendor, iProduct or idProduct, iSerial)
        except IOError:
            return base

    def describe(device):
        """\
        Get a human readable description.
        For USB-Serial devices try to run lsusb to get a human readable description.
        For USB-CDC devices read the description from sysfs.
        """
        base = os.path.basename(device)
        # USB-Serial devices
        sys_dev_path = '/sys/class/tty/%s/device/driver/%s' % (base, base)
        if os.path.exists(sys_dev_path):
            sys_usb = os.path.dirname(os.path.dirname(os.path.realpath(sys_dev_path)))
            return usb_lsusb_string(sys_usb)
        # USB-CDC devices
        sys_dev_path = '/sys/class/tty/%s/device/interface' % (base,)
        if os.path.exists(sys_dev_path):
            return read_line(sys_dev_path)
        return base

    def hwinfo(device):
        """Try to get a HW identification using sysfs"""
        base = os.path.basename(device)
        if os.path.exists('/sys/class/tty/%s/device' % (base,)):
            # PCI based devices
            sys_id_path = '/sys/class/tty/%s/device/id' % (base,)
            if os.path.exists(sys_id_path):
                return read_line(sys_id_path)
            # USB-Serial devices
            sys_dev_path = '/sys/class/tty/%s/device/driver/%s' % (base, base)
            if os.path.exists(sys_dev_path):
                sys_usb = os.path.dirname(os.path.dirname(os.path.realpath(sys_dev_path)))
                return usb_sysfs_hw_string(sys_usb)
            # USB-CDC devices
            if base.startswith('ttyACM'):
                sys_dev_path = '/sys/class/tty/%s/device' % (base,)
                if os.path.exists(sys_dev_path):
                    return usb_sysfs_hw_string(sys_dev_path + '/..')
        return 'n/a'    # XXX directly remove these from the list?

    def comports():
        devices = glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        return [(d, describe(d), hwinfo(d)) for d in devices]

elif plat == 'cygwin':       # cygwin/win32
    def comports():
        devices = glob.glob('/dev/com*')
        return [(d, d, d) for d in devices]

elif plat[:7] == 'openbsd':    # OpenBSD
    def comports():
        devices = glob.glob('/dev/cua*')
        return [(d, d, d) for d in devices]

elif plat[:3] == 'bsd' or  \
        plat[:7] == 'freebsd':

    def comports():
        devices = glob.glob('/dev/cuad*')
        return [(d, d, d) for d in devices]

elif plat[:6] == 'darwin':   # OS X (confirmed)
    def comports():
        """scan for available ports. return a list of device names."""
        devices = glob.glob('/dev/tty.*')
        return [(d, d, d) for d in devices]

elif plat[:6] == 'netbsd':   # NetBSD
    def comports():
        """scan for available ports. return a list of device names."""
        devices = glob.glob('/dev/dty*')
        return [(d, d, d) for d in devices]

elif plat[:4] == 'irix':     # IRIX
    def comports():
        """scan for available ports. return a list of device names."""
        devices = glob.glob('/dev/ttyf*')
        return [(d, d, d) for d in devices]

elif plat[:2] == 'hp':       # HP-UX (not tested)
    def comports():
        """scan for available ports. return a list of device names."""
        devices = glob.glob('/dev/tty*p0')
        return [(d, d, d) for d in devices]

elif plat[:5] == 'sunos':    # Solaris/SunOS
    def comports():
        """scan for available ports. return a list of device names."""
        devices = glob.glob('/dev/tty*c')
        return [(d, d, d) for d in devices]

elif plat[:3] == 'aix':      # AIX
    def comports():
        """scan for available ports. return a list of device names."""
        devices = glob.glob('/dev/tty*')
        return [(d, d, d) for d in devices]

else:
    raise ImportError("Sorry: no implementation for your platform ('%s') available" % (os.name,))

# test
if __name__ == '__main__':
    for port, desc, hwid in sorted(comports()):
        print "%s: %s [%s]" % (port, desc, hwid)

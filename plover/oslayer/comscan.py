#!/usr/bin/env python

# This code was taken from BITPIM which is under GPL2.

### BITPIM
###
### Copyright (C) 2003-2004 Roger Binns <rogerb@rogerbinns.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the BitPim license as detailed in the LICENSE file.
###
### $Id$


"""Detect and enumerate com(serial) ports

You should close all com ports you have open before calling any
functions in this module.  If you don't they will be detected as in
use.

Call the comscan() function It returns a list with each entry being a
dictionary of useful information.  See the platform notes for what is
in each one.

For your convenience the entries in the list are also sorted into
an order that would make sense to the user.

Platform Notes:
===============

w  Windows9x
W  WindowsNT/2K/XP
L  Linux
M  Mac

wWLM name               string   Serial device name
wWLM available          Bool     True if it is possible to open this device
wW   active             Bool     Is the driver actually running?  An example of when this is False
                                 is USB devices or Bluetooth etc that aren't currently plugged in.
                                 If you are presenting stuff for users, do not show entries where
                                 this is false
w    driverstatus       dict     status is some random number, problem is non-zero if there is some
                                 issue (eg device disabled)
wW   hardwareinstance   string   instance of the device in the registry as named by Windows
wWLM description        string   a friendly name to show users
wW   driverdate         tuple    (year, month, day)
 W   driverversion      string   version string
wW   driverprovider     string   the manufacturer of the device driver
wW   driverdescription  string   some generic description of the driver
  L  device             tuple    (major, minor) device specification
  L  driver             string   the driver name from /proc/devices (eg ttyS or ttyUSB)
"""

from __future__ import with_statement

version = "$Revision$"

import sys
import os
import glob


def _IsWindows():
    return sys.platform == 'win32'


def _IsLinux():
    return sys.platform.startswith('linux')


def _IsMac():
    return sys.platform.startswith('darwin')


if _IsWindows():
    import _winreg
    import win32file
    import win32con

    class RegistryAccess:
        "A class that is significantly easier to use to access the Registry"
        def __init__(self, hive=_winreg.HKEY_LOCAL_MACHINE):
            self.rootkey = _winreg.ConnectRegistry(None, hive)

        def getchildren(self, key):
            """Returns a list of the child nodes of a key"""
            k = _winreg.OpenKey(self.rootkey, key)
            index = 0
            res = []
            while 1:
                try:
                    subkey = _winreg.EnumKey(k, index)
                    res.append(subkey)
                    index += 1
                except:
                    # ran out of keys
                    break
            return res

        def safegetchildren(self, key):
            """Doesn't throw exception if doesn't exist

            @return: A list of zero or more items"""
            try:
                k = _winreg.OpenKey(self.rootkey, key)
            except:
                return []
            index = 0
            res = []
            while 1:
                try:
                    subkey = _winreg.EnumKey(k, index)
                    res.append(subkey)
                    index += 1
                except WindowsError, e:
                    if e[0] == 259:  # No more data is available
                        break
                    elif e[0] == 234:  # more data is available
                        index += 1
                        continue
                    raise
            return res

        def getvalue(self, key, node):
            """Gets a value

            The result is returned as the correct type (string, int, etc)"""
            k = _winreg.OpenKey(self.rootkey, key)
            v, t = _winreg.QueryValueEx(k, node)
            if t == 2:
                return int(v)
            if t == 3:
                # lsb data
                res = 0
                mult = 1
                for i in v:
                    res += ord(i) * mult
                    mult *= 256
                return res
            # un unicode if possible
            if isinstance(v, unicode):
                try:
                    return str(v)
                except:
                    pass
            return v

        def safegetvalue(self, key, node, default=None):
            """Gets a value and if nothing is found returns the default"""
            try:
                return self.getvalue(key, node)
            except:
                return default

        def findkey(self, start, lookfor, prependresult=""):
            """Searches for the named key"""
            res = []
            for i in self.getchildren(start):
                if i == lookfor:
                    res.append(prependresult + i)
                else:
                    l = self.findkey(start + "\\" + i,
                                     lookfor,
                                     prependresult + i + "\\")
                    res.extend(l)
            return res

        def getallchildren(self, start, prependresult=""):
            """Returns a list of all child nodes in the hierarchy"""
            res = []
            for i in self.getchildren(start):
                res.append(prependresult + i)
                l = self.getallchildren(start + "\\" + i,
                                        prependresult + i + "\\")
                res.extend(l)
            return res


def _comscanwindows():
    """Get detail about all com ports on Windows

    This code functions on both win9x and nt/2k/xp"""
    # give results back
    results = {}
    resultscount = 0

    # list of active drivers on win98
    activedrivers = {}

    reg = RegistryAccess(_winreg.HKEY_DYN_DATA)
    k = r"Config Manager\Enum"
    for device in reg.safegetchildren(k):
        hw = reg.safegetvalue(k + "\\" + device, "hardwarekey")
        if hw is None:
            continue
        status = reg.safegetvalue(k + "\\" + device, "status", -1)
        problem = reg.safegetvalue(k + "\\" + device, "problem", -1)
        activedrivers[hw.upper()] = {'status': status, 'problem': problem}

    # list of active drivers on winXP.  Apparently Win2k is different?
    reg = RegistryAccess(_winreg.HKEY_LOCAL_MACHINE)
    k = r"SYSTEM\CurrentControlSet\Services"
    for service in reg.safegetchildren(k):
        # we will just take largest number
        count = int(reg.safegetvalue(k + "\\" + service + "\\Enum",
                                     "Count", 0))
        next = int(reg.safegetvalue(k + "\\" + service + "\\Enum",
                                    "NextInstance", 0))
        for id in range(max(count, next)):
            hw = reg.safegetvalue(k + "\\" + service + "\\Enum", repr(id))
            if hw is None:
                continue
            activedrivers[hw.upper()] = None

    # scan through everything listed in Enum.  Enum is the key containing a
    # list of all running hardware
    reg = RegistryAccess(_winreg.HKEY_LOCAL_MACHINE)

    # The three keys are:
    #
    #  - where to find hardware
    #    This then has three layers of children.
    #    Enum
    #     +-- Category   (something like BIOS, PCI etc)
    #           +-- Driver  (vendor/product ids etc)
    #                 +-- Instance  (An actual device.  You may have more than one instance)
    #
    #  - where to find information about drivers.  The driver name is looked up in the instance
    #    (using the key "driver") and then looked for as a child key of driverlocation to find
    #    out more about the driver
    #
    #  - where to look for the portname key.  Eg in Win98 it is directly in the instance whereas
    #    in XP it is below "Device Parameters" subkey of the instance

    for enumstr, driverlocation, portnamelocation in (
            (r"SYSTEM\CurrentControlSet\Enum",
             r"SYSTEM\CurrentControlSet\Control\Class",
             r"\Device Parameters"),  # win2K/XP
            (r"Enum", r"System\CurrentControlSet\Services\Class", ""),   # win98
            ):
        for category in reg.safegetchildren(enumstr):
            catstr = enumstr + "\\" + category
            for driver in reg.safegetchildren(catstr):
                drvstr = catstr + "\\" + driver
                for instance in reg.safegetchildren(drvstr):
                    inststr = drvstr + "\\" + instance

                    # see if there is a portname
                    name = reg.safegetvalue(inststr + portnamelocation,
                                            "PORTNAME", "")

                    # We only want com ports
                    if len(name) < 4 or name.lower()[:3] != "com":
                        continue

                    # Get rid of phantom devices
                    phantom = reg.safegetvalue(inststr, "Phantom", 0)
                    if phantom:
                        continue

                    # Lookup the class
                    klassguid = reg.safegetvalue(inststr, "ClassGUID")
                    if klassguid is not None:
                        # win2k uses ClassGuid
                        klass = reg.safegetvalue(
                            driverlocation + "\\" + klassguid, "Class")
                    else:
                        # Win9x and WinXP use Class
                        klass = reg.safegetvalue(inststr, "Class")

                    if klass is None:
                        continue
                    klass = klass.lower()
                    if klass == 'ports':
                        klass = 'serial'
                    elif klass == 'modem':
                        klass = 'modem'
                    else:
                        continue

                    # verify COM is followed by digits only
                    try:
                        portnum = int(name[3:])
                    except:
                        continue

                    # we now have some sort of match
                    res = {}

                    res['name'] = name.upper()
                    res['class'] = klass

                    # is the device active?
                    kp = inststr[len(enumstr) + 1:].upper()
                    if kp in activedrivers:
                        res['active'] = True
                        if activedrivers[kp] is not None:
                            res['driverstatus'] = activedrivers[kp]
                    else:
                        res['active'] = False

                    # available?
                    if res['active']:
                        try:
                            usename = name
                            if (sys.platform == 'win32'
                                and name.lower().startswith("com")):
                                usename = "\\\\?\\" + name
                            ComPort = win32file.CreateFile(
                                usename,
                                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                                0, None,
                                win32con.OPEN_EXISTING,
                                win32con.FILE_ATTRIBUTE_NORMAL,
                                None,
                            )
                            win32file.CloseHandle(ComPort)
                            res['available'] = True
                        except Exception, e:
                            print usename, "is not available", e
                            res['available'] = False
                    else:
                        res['available'] = False

                    # hardwareinstance
                    res['hardwareinstance'] = kp

                    # friendly name
                    res['description'] = reg.safegetvalue(
                        inststr, "FriendlyName", "<No Description>")

                    # driver information key
                    drv = reg.safegetvalue(inststr, "Driver")

                    if drv is not None:
                        driverkey = driverlocation + "\\" + drv

                        # get some useful driver information
                        for subkey, reskey in (
                            ("driverdate", "driverdate"),
                            ("providername", "driverprovider"),
                            ("driverdesc", "driverdescription"),
                            ("driverversion", "driverversion")):
                            val = reg.safegetvalue(driverkey, subkey, None)
                            if val is None:
                                continue
                            if reskey == "driverdate":
                                try:
                                    val2 = val.split('-')
                                    val = (int(val2[2]),
                                           int(val2[0]),
                                           int(val2[1]),
                                          )
                                except:
                                    # ignore weird dates
                                    continue
                            res[reskey] = val

                    results[resultscount] = res
                    resultscount += 1

    return results


# There follows a demonstration of how user friendly Linux is.
# Users are expected by some form of magic to know exactly what
# the names of their devices are.  We can't even tell the difference
# between a serial port not existing, and there not being sufficient
# permission to open it
def _comscanlinux(maxnum=9):
    """Get all the ports on Linux

    Note that Linux doesn't actually provide any way to enumerate actual ports.
    Consequently we just look for device nodes.  It still isn't possible to
    establish if there are actual device drivers behind them.  The availability
    testing is done however.

    @param maxnum: The highest numbered device to look for (eg maxnum of 17
                   will look for ttyS0 ... ttys17)
    """

    # track of mapping majors to drivers
    drivers = {}

    # get the list of char drivers from /proc/drivers
    with file('/proc/devices', 'r') as f:
        f.readline()  # skip "Character devices:" header
        for line in f.readlines():
            line = line.split()
            if len(line) != 2:
                break  # next section
            major, driver = line
            drivers[int(major)] = driver

    # device nodes we have seen so we don't repeat them in listing
    devcache = {}

    resultscount = 0
    results = {}
    for prefix, description, klass in (
        ("/dev/cua", "Standard serial port", "serial"),
        ("/dev/ttyUSB", "USB to serial convertor", "serial"),
        ("/dev/ttyACM", "USB modem", "modem"),
        ("/dev/rfcomm", "Bluetooth", "modem"),
        ("/dev/usb/ttyUSB", "USB to serial convertor", "serial"),
        ("/dev/usb/tts/", "USB to serial convertor", "serial"),
        ("/dev/usb/acm/", "USB modem", "modem"),
        ("/dev/input/ttyACM", "USB modem", "modem")
        ):
        for num in range(maxnum + 1):
            name = prefix + repr(num)
            if not os.path.exists(name):
                continue
            res = {}
            res['name'] = name
            res['class'] = klass
            res['description'] = description + " (" + name + ")"
            dev = os.stat(name).st_rdev
            try:
                with file(name, 'rw'):
                    res['available'] = True
            except:
                res['available'] = False
            # linux specific, and i think they do funky stuff on kernel 2.6
            # there is no way to get these 'normally' from the python library
            major = (dev >> 8) & 0xff
            minor = dev & 0xff
            res['device'] = (major, minor)
            if major in drivers:
                res['driver'] = drivers[major]

            if res['available']:
                if dev not in devcache or not devcache[dev][0]['available']:
                    results[resultscount] = res
                    resultscount += 1
                    devcache[dev] = [res]
                continue
            # not available, so add
            try:
                devcache[dev].append(res)
            except:
                devcache[dev] = [res]
    # add in one failed device type per major/minor
    for dev in devcache:
        if devcache[dev][0]['available']:
            continue
        results[resultscount] = devcache[dev][0]
        resultscount += 1
    return results


def _comscanmac():
    """Get all the ports on Mac

    Just look for /dev/cu.* entries, they all seem to populate here whether
    USB->Serial, builtin, bluetooth, etc...

    """

    resultscount = 0
    results = {}
    for name in glob.glob("/dev/cu.*"):
        res = {}
        res['name'] = name
        if name.upper().rfind("MODEM") >= 0:
            res['description'] = "Modem" + " (" + name + ")"
            res['class'] = "modem"
        else:
            res['description'] = "Serial" + " (" + name + ")"
            res['class'] = "serial"
        try:
            with file(name, 'rw'):
                res['available'] = True
        except:
            res['available'] = False
        results[resultscount] = res
        resultscount += 1
    return results


def _stringint(str):
    """Seperate a string and trailing number into a tuple

    For example "com10" returns ("com", 10)
    """
    prefix = str
    suffix = ""

    while len(prefix) and prefix[-1] >= '0' and prefix[-1] <= '9':
        suffix = prefix[-1] + suffix
        prefix = prefix[:-1]

    if len(suffix):
        return (prefix, int(suffix))
    else:
        return (prefix, None)


def _cmpfunc(a, b):
    """Comparison function for two port names

    In particular it looks for a number on the end, and sorts by the prefix (as
    a string operation) and then by the number.  This function is needed
    because "com9" needs to come before "com10"
    """

    aa = _stringint(a[0])
    bb = _stringint(b[0])

    if aa == bb:
        if a[1] == b[1]:
            return 0
        if a[1] < b[1]:
            return -1
        return 1
    if aa < bb:
        return -1
    return 1


def comscan(*args, **kwargs):
    """Call platform specific version of comscan function"""
    res = {}
    if _IsWindows():
        res = _comscanwindows(*args, **kwargs)
    elif _IsLinux():
        res = _comscanlinux(*args, **kwargs)
    elif _IsMac():
        res = _comscanmac(*args, **kwargs)
    else:
        raise Exception("unknown platform " + sys.platform)

    # sort by name
    keys = res.keys()
    declist = [(res[k]['name'], k) for k in keys]
    declist.sort(_cmpfunc)

    return [res[k[1]] for k in declist]


if __name__ == "__main__":
    res = comscan()

    output = "ComScan " + version + "\n\n"

    for r in res:
        rkeys = r.keys()
        rkeys.sort()

        output += r['name'] + ":\n"
        offset = 0
        for rk in rkeys:
            if rk == 'name':
                continue
            v = r[rk]
            if not isinstance(v, type("")):
                v = repr(v)
            op = ' %s: %s ' % (rk, v)
            if offset + len(op) > 78:
                output += "\n" + op
                offset = len(op) + 1
            else:
                output += op
                offset += len(op)

        if output[-1] != "\n":
            output += "\n"
        output += "\n"
        offset = 0

    print output

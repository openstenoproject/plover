from contextlib import contextmanager
import ctypes.util
import os
import logging

from plover import log, __name__ as __software_name__
from plover.oslayer.config import ASSETS_DIR


APPNAME = ctypes.c_char_p(__software_name__.capitalize().encode())
APPICON = ctypes.c_char_p(os.path.join(ASSETS_DIR, 'plover.png').encode())
SERVICE = ctypes.c_char_p(b'org.freedesktop.Notifications')
INTERFACE = ctypes.c_char_p(b'/org/freedesktop/Notifications')

NOTIFY_URGENCY_LOW = ctypes.c_uint8(0)
NOTIFY_URGENCY_NORMAL = ctypes.c_uint8(1)
NOTIFY_URGENCY_CRITICAL = ctypes.c_uint8(2)

DBUS_BUS_SESSION = ctypes.c_uint(0)

DBUS_TYPE_ARRAY      = ctypes.c_int(ord('a'))
DBUS_TYPE_BYTE       = ctypes.c_int(ord('y'))
DBUS_TYPE_DICT_ENTRY = ctypes.c_int(ord('e'))
DBUS_TYPE_INT32      = ctypes.c_int(ord('i'))
DBUS_TYPE_STRING     = ctypes.c_int(ord('s'))
DBUS_TYPE_UINT32     = ctypes.c_int(ord('u'))
DBUS_TYPE_VARIANT    = ctypes.c_int(ord('v'))


def ctypes_func(library, signature):
    restype, func_name, *argtypes = signature.split()
    func = getattr(library, func_name)
    setattr(func, 'argtypes', [
        ctypes.POINTER(getattr(ctypes, 'c_' + t[1:]))
        if t.startswith('&') else getattr(ctypes, 'c_' + t)
        for t in argtypes
    ])
    setattr(func, 'restype',
            None if restype == 'void' else
            getattr(ctypes, 'c_' + restype))
    return func


class DbusNotificationHandler(logging.Handler):
    """ Handler using DBus notifications to show messages. """

    def __init__(self):
        super().__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('<b>%(levelname)s:</b> %(message)s'))

        libname = ctypes.util.find_library('dbus-1')
        if libname is None:
            raise FileNotFoundError('dbus-1 library')
        library = ctypes.cdll.LoadLibrary(libname)

        bus_get = ctypes_func(library, 'void_p dbus_bus_get uint void_p')
        message_new = ctypes_func(library, 'void_p dbus_message_new_method_call char_p char_p char_p char_p')
        message_unref = ctypes_func(library, 'void dbus_message_unref void_p')
        iter_init_append = ctypes_func(library, 'void dbus_message_iter_init_append void_p void_p')
        iter_append_basic = ctypes_func(library, 'bool dbus_message_iter_append_basic void_p int void_p')
        iter_open_container = ctypes_func(library, 'bool dbus_message_iter_open_container void_p int char_p void_p')
        iter_close_container = ctypes_func(library, 'bool dbus_message_iter_close_container void_p void_p')
        connection_send = ctypes_func(library, 'bool dbus_connection_send void_p void_p &uint32')

        # Need message + container + dict_entry + variant = 4 iterators.
        self._iter_stack = [ctypes.create_string_buffer(128) for __ in range(4)]
        self._iter_stack_index = 0

        @contextmanager
        def open_container(kind, signature):
            parent_iter = self._iter_stack[self._iter_stack_index]
            sub_iter = self._iter_stack[self._iter_stack_index + 1]
            if not iter_open_container(parent_iter, kind, signature, sub_iter):
                raise MemoryError
            self._iter_stack_index += 1
            try:
                yield
            finally:
                if not iter_close_container(parent_iter, sub_iter):
                    raise MemoryError
                self._iter_stack_index -= 1

        def append_basic(kind, value):
            if not iter_append_basic(self._iter_stack[self._iter_stack_index], kind, ctypes.byref(value)):
                raise MemoryError

        bus = bus_get(DBUS_BUS_SESSION, None)

        actions_signature = ctypes.c_char_p(b's')
        hints_signature = ctypes.c_char_p(b'{sv}')
        notify_str = ctypes.c_char_p(b'Notify')
        urgency_signature = ctypes.c_char_p(b'y')
        urgency_str = ctypes.c_char_p(b'urgency')
        zero = ctypes.c_uint(0)

        def notify(body, urgency, timeout):
            message = message_new(SERVICE, INTERFACE, SERVICE, notify_str)
            try:
                iter_init_append(message, self._iter_stack[self._iter_stack_index])
                # app_name
                append_basic(DBUS_TYPE_STRING, APPNAME)
                # replaces_id
                append_basic(DBUS_TYPE_UINT32, zero)
                # app_icon
                append_basic(DBUS_TYPE_STRING, APPICON)
                # summary
                append_basic(DBUS_TYPE_STRING, APPNAME)
                # body
                append_basic(DBUS_TYPE_STRING, body)
                # actions
                with open_container(DBUS_TYPE_ARRAY, actions_signature):
                    pass
                # hints
                with open_container(DBUS_TYPE_ARRAY, hints_signature), open_container(DBUS_TYPE_DICT_ENTRY, None):
                    append_basic(DBUS_TYPE_STRING, urgency_str)
                    with open_container(DBUS_TYPE_VARIANT, urgency_signature):
                        append_basic(DBUS_TYPE_BYTE, urgency)
                # expire_timeout
                append_basic(DBUS_TYPE_INT32, timeout)
                connection_send(bus, message, None)
            finally:
                message_unref(message)

        self._notify = notify

    def emit(self, record):
        level = record.levelno
        message = self.format(record)
        if message.endswith('\n'):
            message = message[:-1]
        if level <= log.INFO:
            timeout = 10
            urgency = NOTIFY_URGENCY_LOW
        elif level <= log.WARNING:
            timeout = 15
            urgency = NOTIFY_URGENCY_NORMAL
        else:
            timeout = 0
            urgency = NOTIFY_URGENCY_CRITICAL
        self._notify(ctypes.c_char_p(message.encode()), urgency, ctypes.c_int(timeout * 1000))

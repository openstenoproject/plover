# Copyright (c) 2011 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for stentura.py."""

import array
import struct
import threading
import unittest

from plover.machine import stentura


def make_response(seq, action, error=0, p1=0, p2=0, data=None,
                  length=None):
    if not length:
        length = 14
        if data:
            length += 2 + len(data)
    response = struct.pack('<2B5H', 1, seq, length, action, error, p1, p2)
    crc = stentura._crc(buffer(response, 1, 11))
    response += struct.pack('<H', crc)
    if data:
        crc = stentura._crc(data)
        if not isinstance(data, str) and not isinstance(data, buffer):
            data = ''.join([chr(b) for b in data])
        response += data + struct.pack('<H', crc)
    return response


def make_read_response(seq, data=[]):
    return make_response(seq, stentura._READC, p1=len(data), data=data)


def make_readc_packets(data):
    requests, responses = [], []
    seq = stentura._SequenceCounter()
    buf = array.array('B')
    block, byte = 0, 0
    while data:
        s = seq()
        chunk = buffer(data, 0, 512)
        data = buffer(data, 512)
        q = stentura._make_read(buf, s, block, byte)
        requests.append(str(q))
        r = make_read_response(s, chunk)
        responses.append(str(r))
        byte += len(chunk)
        if byte >= 512:
            block += 1
            byte -= 512
    s = seq()
    q = stentura._make_read(buf, s, block, byte)
    requests.append(str(q))
    r = make_read_response(s)
    responses.append(str(r))
    return requests, responses


def parse_request(request):
    header = struct.unpack_from('<2B8H', request)
    if header[2] > 18:
        header = list(header) + [request[18:-2], struct.unpack('<H',
                                                               request[-2:])]
    else:
        header = list(header) + [None] * 2
    return dict(zip(['SOH', 'seq', 'length', 'action', 'p1', 'p2',
                     'p3', 'p4', 'p5', 'crc', 'data', 'data_crc'], header))


class MockPacketPort(object):
    def __init__(self, responses, requests=None):
        self._responses = responses
        self.writes = 0
        self._requests = requests
        self._current_response_offset = None

    def write(self, data):
        self.writes += 1
        if self._requests and self._requests[self.writes - 1] != str(data):
            raise Exception("Wrong packet.")
        self._current_response_offset = 0
        return len(data)

    def read(self, count):
        response = self._responses[self.writes - 1]
        data = buffer(response, self._current_response_offset, count)
        self._current_response_offset += count
        return data


class TestCase(unittest.TestCase):
    def test_crc(self):
        data = [ord(x) for x in '123456789']
        self.assertEqual(stentura._crc(data), 0xBB3D)

    def test_write_buffer(self):
        buf = array.array('B')
        data = [1, 2, 3]
        stentura._write_to_buffer(buf, 0, data)
        self.assertSequenceEqual(buf, data)
        stentura._write_to_buffer(buf, 0, [5, 6])
        self.assertSequenceEqual(buf, [5, 6, 3])

    def test_parse_stroke(self):
        # SAT
        a = 0b11001000
        b = 0b11000100
        c = 0b11000000
        d = 0b11001000
        self.assertItemsEqual(stentura._parse_stroke(a, b, c, d),
                              ['S-', 'A-', '-T'])

# 11^#STKP 11WHRAO* 11EUFRPB 11LGTSDZ
# PRAOERBGS
    def test_parse_strokes(self):
        data = []
        # SAT
        a = 0b11001000
        b = 0b11000100
        c = 0b11000000
        d = 0b11001000
        data.extend([a, b, c, d])
        # PRAOERBGS
        a = 0b11000001
        b = 0b11001110
        c = 0b11100101
        d = 0b11010100
        data.extend([a, b, c, d])
        strokes = stentura._parse_strokes(''.join([chr(b) for b in data]))
        expected = [['S-', 'A-', '-T'],
                    ['P-', 'R-', 'A-', 'O-', '-E', '-R', '-B', '-G', '-S']]
        for i, stroke in enumerate(strokes):
            self.assertItemsEqual(stroke, expected[i])

    def test_make_request(self):
        buf = array.array('B')
        seq = 2
        action = stentura._OPEN
        p1, p2, p3, p4, p5 = 1, 2, 3, 4, 5
        p = stentura._make_request(buf, action, seq, p1, p2, p3, p4, p5)
        for_crc = [seq, 18, 0, action, 0, p1, 0, p2, 0, p3, 0, p4, 0, p5, 0]
        crc = stentura._crc(for_crc)
        expected = [1] + for_crc + [crc & 0xFF, crc >> 8]
        self.assertSequenceEqual(p, [chr(b) for b in expected])

        # Now with data.
        data = 'Testing Testing 123'
        p = stentura._make_request(buf, action, seq, p1, p2, p3, p4, p5, data)
        length = 18 + len(data) + 2
        for_crc = [seq, length & 0xFF, length >> 8, action, 0,
                   p1, 0, p2, 0, p3, 0, p4, 0, p5, 0]
        crc = stentura._crc(for_crc)
        data_crc = stentura._crc(data)
        expected = ([1] + for_crc + [crc & 0xFF, crc >> 8] +
                    [ord(b) for b in data] + [data_crc & 0xFF, data_crc >> 8])
        self.assertSequenceEqual(p, [chr(b) for b in expected])

    def test_make_open(self):
        buf = array.array('B', [3] * 18)  # Start with junk in the buffer.
        seq = 79
        drive = 'A'
        filename = 'REALTIME.000'
        p = stentura._make_open(buf, seq, drive, filename)
        for_crc = [seq, 20 + len(filename), 0, stentura._OPEN, 0, ord(drive),
                   0, 0, 0, 0, 0, 0, 0, 0, 0]
        crc = stentura._crc(for_crc)
        data_crc = stentura._crc(filename)
        expected = ([1] + for_crc + [crc & 0xFF, crc >> 8] +
                    [ord(b) for b in filename] +
                    [data_crc & 0xFF, data_crc >> 8])
        self.assertSequenceEqual(p, [chr(b) for b in expected])

    def test_make_read(self):
        buf = array.array('B', [3] * 20)  # Start with junk in the buffer.
        seq = 32
        block = 1
        byte = 8
        length = 20
        p = stentura._make_read(buf, seq, block, byte, length)
        for_crc = [seq, 18, 0, stentura._READC, 0, 1, 0, 0, 0, length, 0,
                   block, 0, byte, 0]
        crc = stentura._crc(for_crc)
        expected = [1] + for_crc + [crc & 0xFF, crc >> 8]
        self.assertSequenceEqual(p, [chr(b) for b in expected])

    def test_make_reset(self):
        buf = array.array('B', [3] * 20)  # Start with junk in the buffer.
        seq = 67
        p = stentura._make_reset(buf, seq)
        for_crc = [seq, 18, 0, stentura._RESET, 0] + ([0] * 10)
        crc = stentura._crc(for_crc)
        expected = [1] + for_crc + [crc & 0xFF, crc >> 8]
        self.assertSequenceEqual(p, [chr(b) for b in expected])

    def test_validate_response(self):
        tests = [
            (make_response(5, 9, 1, 2, 3), True, "valid no data"),
            (make_response(5, 9, 1, 2, 3, data="hello"), True, "valid, data"),
            (make_response(5, 9, 1, 2, 3)[:12], False, "short"),
            (make_response(5, 9, 1, 2, 3, length=15), False, "Length long"),
            (make_response(5, 9, 1, 2, 3, data='foo', length=15), False,
             "Length short"),
            (make_response(5, 9, 1, 2, 3) + '1', False, "Bad data"),
            (make_response(5, 9, 1, 2, 3)[:-1] + '1', False, "bad crc"),
            (make_response(5, 9, 1, 2, 3, data='foo')[:-1] + '1', False,
             "bad data crc")
        ]
        for test in tests:
            self.assertEqual(stentura._validate_response(
                test[0]), test[1], test[2])

    def test_read_data_simple(self):
        class MockPort(object):
            def read(self, count):
                if count != 5:
                    raise Exception("Incorrect number read.")
                return "12345"

        port = MockPort()
        buf = array.array('B')
        count = stentura._read_data(port, threading.Event(), buf, 0, 5)
        self.assertEqual(count, 5)
        self.assertSequenceEqual([chr(b) for b in buf], "12345")

        # Test the offset parameter.
        count = stentura._read_data(port, threading.Event(), buf, 4, 5)
        self.assertSequenceEqual([chr(b) for b in buf], "123412345")

    def test_read_data_stop_set(self):
        class MockPort(object):
            def read(self, count):
                return "0000"
        buf = array.array('B')
        event = threading.Event()
        event.set()
        with self.assertRaises(stentura._StopException):
            stentura._read_data(MockPort(), event, buf, 0, 4)

    def test_read_data_timeout(self):
        class MockPort(object):
            def read(self, count):
                # When serial time out occurs read() returns
                # less characters as requested
                return "123";

        port = MockPort()
        buf = array.array('B')
        with self.assertRaises(stentura._TimeoutException):
            stentura._read_data(port, threading.Event(), buf, 0, 4)

    def test_read_packet_simple(self):
        class MockPort(object):
            def __init__(self, packet):
                self._packet = packet

            def read(self, count):
                requested_bytes = buffer(self._packet, 0, count)
                self._packet = self._packet[count:]
                return requested_bytes

        buf = array.array('B')
        for packet in [make_response(1, 2, 3, 4, 5),
                       make_response(1, 2, 3, 4, 5, "hello")]:
            port = MockPort(packet)
            response = stentura._read_packet(port, threading.Event(), buf)
            self.assertSequenceEqual(response, packet)

    def test_read_packet_fail(self):
        class MockPort(object):
            def __init__(self, data_section_length=0, set1=False, set2=False,
                         give_too_much_data=False, give_timeout=False):
                self._set1 = set1
                self._set2 = set2
                self._read1 = False
                self._read2 = False
                self.event = threading.Event()
                self._give_timeout = give_timeout;
                self._data = ([1, 0, data_section_length + 4, 0] +
                              [0] * data_section_length)
                if give_too_much_data:
                    self._data.append(0)
                self._data = ''.join([chr(b) for b in self._data])

            def read(self, count):
                if not self._read1:
                    self._read1 = True
                    if self._set1:
                        self.event.set()
                elif not self._read2:
                    self._read2 = True
                    if self._set2:
                        self.event.set()
                else:
                    raise Exception("Already read data.")
                if self._give_timeout and len(self._data) == count:
                    # If read() returns less bytes what was requested,
                    # it indicates a timeout.
                    count -= 1
                requested_bytes = buffer(self._data, 0, count);
                self._data = self._data[count:]
                return requested_bytes

        buf = array.array('B')

        with self.assertRaises(stentura._StopException):
            port = MockPort(set1=True)
            stentura._read_packet(port, port.event, buf)

        with self.assertRaises(stentura._StopException):
            port = MockPort(data_section_length=30, set2=True)
            stentura._read_packet(port, port.event, buf)

        with self.assertRaises(stentura._TimeoutException):
            port = MockPort(give_timeout=True)
            stentura._read_packet(port, port.event, buf)

        with self.assertRaises(stentura._TimeoutException):
            port = MockPort(data_section_length=30, give_timeout=True)
            stentura._read_packet(port, port.event, buf)

        with self.assertRaises(stentura._ProtocolViolationException):
            port = MockPort(give_too_much_data=True)
            stentura._read_packet(port, port.event, buf)

    def test_write_to_port(self):
        class MockPort(object):
            def __init__(self, chunk):
                self._chunk = chunk
                self.data = ''

            def write(self, data):
                data = data[:self._chunk]
                self.data += data
                return len(data)

        data = ''.join([chr(b) for b in xrange(20)])

        # All in one shot.
        port = MockPort(20)
        stentura._write_to_port(port, data)
        self.assertSequenceEqual(data, port.data)

        # In parts.
        port = MockPort(5)
        stentura._write_to_port(port, data)
        self.assertSequenceEqual(data, port.data)

    def test_send_receive(self):
        event = threading.Event()
        buf, seq, action = array.array('B'), 5, stentura._OPEN
        request = stentura._make_request(array.array('B'), stentura._OPEN, seq)
        correct_response = make_response(seq, action)
        wrong_seq = make_response(seq - 1, action)
        wrong_action = make_response(seq, action + 1)
        bad_response = make_response(seq, action, data="foo", length=15)

        # Correct response first time.
        responses = [correct_response]
        port = MockPacketPort(responses)
        response = stentura._send_receive(port, event, request, buf)
        self.assertSequenceEqual(response, correct_response)

        # Timeout once then correct response.
        responses = ['', correct_response]
        port = MockPacketPort(responses)
        response = stentura._send_receive(port, event, request, buf)
        self.assertSequenceEqual(response, correct_response)

        # Wrong sequence number then correct response.
        responses = [wrong_seq, correct_response]
        port = MockPacketPort(responses)
        response = stentura._send_receive(port, event, request, buf)
        self.assertSequenceEqual(response, correct_response)

        # No correct responses. Also make sure max_retries is honored.
        max_tries = 6
        responses = [''] * max_tries
        port = MockPacketPort(responses)
        with self.assertRaises(stentura._ConnectionLostException):
            stentura._send_receive(port, event, request, buf, max_tries)
        self.assertEqual(max_tries, port.writes)

        # Wrong action.
        responses = [wrong_action]
        port = MockPacketPort(responses)
        with self.assertRaises(stentura._ProtocolViolationException):
            stentura._send_receive(port, event, request, buf)

        # Bad packet.
        responses = [bad_response]
        port = MockPacketPort(responses)
        with self.assertRaises(stentura._ProtocolViolationException):
            stentura._send_receive(port, event, request, buf)

        # Stopped.
        responses = ['']
        event.set()
        port = MockPacketPort(responses)
        with self.assertRaises(stentura._StopException):
            stentura._send_receive(port, event, request, buf)

    def test_sequence_counter(self):
        seq = stentura._SequenceCounter()
        actual = [seq() for x in xrange(512)]
        expected = range(256) * 2
        self.assertEqual(actual, expected)

        seq = stentura._SequenceCounter(67)
        actual = [seq() for x in xrange(512)]
        expected = range(67, 256) + range(256) + range(67)
        self.assertEqual(actual, expected)

    def test_read(self):
        request_buf = array.array('B')
        response_buf = array.array('B')
        stroke_buf = array.array('B')
        event = threading.Event()

        tests = ([0b11000001] * (3 * 512 + 28), [0b11010101] * 4,
                 [0b11000010] * 8)

        for data in tests:
            data = str(buffer(array.array('B', data)))
            requests, responses = make_readc_packets(data)
            port = MockPacketPort(responses, requests)
            seq = stentura._SequenceCounter()
            block, byte = 0, 0
            block, byte, response = stentura._read(port, event, seq, request_buf,
                                      response_buf, stroke_buf, block, byte)
            self.assertEqual(data, str(response))
            self.assertEqual(block, len(data) / 512)
            self.assertEqual(byte, len(data) % 512)

    def test_loop(self):
        class Event(object):
            def __init__(self, count, data, stop=False):
                self.count = count
                self.data = data
                self.stop = stop
                
            def __repr__(self):
                return '<{}, {}, {}>'.format(self.count, self.data, self.stop)

        class MockPort(object):
            def __init__(self, events=[]):
                self._file = ''
                self._out = ''
                self._is_open = False
                self.event = threading.Event()
                self.count = 0
                self.events = [Event(*x) for x in
                               sorted(events, key=lambda x: x[0])]

            def write(self, request):
                # Process the packet and put together a response.
                p = parse_request(request)
                if p['action'] == stentura._OPEN:
                    self._out = make_response(p['seq'], p['action'])
                    self._is_open = True
                elif p['action'] == stentura._READC:
                    if not self._is_open:
                        raise Exception("no open")
                    length, block, byte = p['p3'], p['p4'], p['p5']
                    seq = p['seq']
                    action = stentura._READC
                    start = block * 512 + byte
                    end = start + length
                    data = self._file[start:end]
                    self._out = make_response(seq, action, p1=len(data),
                                              data=data)
                while self.events and self.events[0].count <= self.count:
                    event = self.events.pop(0)
                    self.append(event.data)
                    if event.stop:
                        self.event.set()
                self.count += 1
                return len(request)

            def read(self, count):
                requested_bytes = buffer(self._out,0 , count)
                self._out = self._out[count:]
                return requested_bytes

            def append(self, data):
                self._file += data
                return self

            def flushInput(self):
                pass

            def flushOutput(self):
                pass

        data1 = ''.join([chr(b) for b in [0b11001010] * 4 * 9])
        data1_trans = [['S-', 'K-', 'R-', 'O-', '-F', '-P', '-T', '-D']] * 9
        data2 = ''.join([chr(b) for b in [0b11001011] * 4 * 30])

        tests = [
            # No inputs but nothing crashes either.
            (MockPort([(30, '', True)]), []),
            # A few strokes.
            (MockPort([(23, data1), (43, '', True)]), data1_trans),
            # Ignore data that's there before we started.
            (MockPort([(46, '', True)]).append(data2), []),
            # Ignore data that was there and also parse some strokes.
            (MockPort([(25, data1), (36, '', True)]).append(data2), data1_trans)
        ]

        for test in tests:
            read_data = []

            def callback(data):
                read_data.append(data)

            port = test[0]
            expected = test[1]
            
            ready_called = [False]
            def ready():
                ready_called[0] = True
            
            try:
                ready_called[0] = False
                stentura._loop(port, port.event, callback, ready)
            except stentura._StopException:
                pass
            self.assertEqual(read_data, expected)
            self.assertTrue(ready_called[0])

# TODO: add a test on the machine itself with mocks

if __name__ == '__main__':
    unittest.main()

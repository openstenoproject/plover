# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.
#
# TODO: Convert non-ascii characters to UTF8
# TODO: What does ^ mean in Eclipse?
# TODO: What does #N mean in Eclipse?
# TODO: convert supported commands from Eclipse

"""Parsing an RTF/CRE dictionary.

RTF/CRE spec:
http://www.legalxml.org/workgroups/substantive/transcripts/cre-spec.htm

"""

import inspect
import re
from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary

# A regular expression to capture an individual entry in the dictionary.
DICT_ENTRY_PATTERN = re.compile(r'(?s)(?<!\\){\\\*\\cxs (?P<steno>[^}]+)}' + 
                                r'(?P<translation>.*?)(?:(?<!\\)\r\n)*?'
                                r'(?=(?:(?<!\\){\\\*\\cxs [^}]+})|' +
                                r'(?:(?:(?<!\\)\r\n\s*)*}\s*\Z))')

class TranslationConverter(object):
    
    def __init__(self):
        handler_funcs = inspect.getmembers(self, inspect.ismethod)
        handlers = [self._make_re_handler(f.__doc__, f)
                    for name, f in handler_funcs 
                    if name.startswith('_re_handle_')]
        handlers.append(self._match_nested_command_group)
        def handler(s, pos):
            for handler in handlers:
                result = handler(s, pos)
                if result:
                    return result
            return None
        self._handler = handler
        self._command_pattern = re.compile(
            r'(\\\*)?\\([a-z]+)(-?[0-9]+)?[ ]?')
        self._multiple_whitespace_pattern = re.compile(r'([ ]{2,})')
        self._whitespace = True
    
    def _make_re_handler(self, pattern, f):
        pattern = re.compile(pattern)
        def handler(s, pos):
            match = pattern.match(s, pos)
            if match:
                newpos = match.end()
                result = f(match)
                return (newpos, result)
            return None
        return handler

    def _re_handle_escapedchar(self, m):
        r'\\([-\\{}])'
        return m.group(1)
        
    def _re_handle_hardspace(self, m):
        r'\\~'
        return '{^ ^}'
        
    def _re_handle_dash(self, m):
        r'\\_'
        return '-'
        
    def _re_handle_escaped_newline(self, m):
        r'\\\r\n'
        return '{#Return}{#Return}'
        
    def _re_handle_commands(self, m):
        r'(\\\*)?\\([a-z]+)(-?[0-9]+)?[ ]?'
        
        ignore = bool(m.group(1))
        command = m.group(2)
        
        if command == 'cxds':
            return '{^}'
        
        if command == 'cxfc':
            return '{-|}'

        if command == 'cxfl':
            # Force lower case is not yet supported by plover.
            return ''

        if command == 'par':
            return '{#Return}{#Return}'

        # Unrecognized commands are ignored.
        return ''

    def _re_handle_simple_command_group(self, m):
        r'{(\\\*)?\\([a-z]+)(-?[0-9]+)?[ ]?([^{}]*)}'
        
        ignore = bool(m.group(1))
        command = m.group(2)
        contents = m.group(4)
        if contents is None:
            contents = ''

        if command == 'cxstit':
            # Plover doesn't support stitching.
            return self(contents)
        
        if command == 'cxfing':
            prev = self._whitespace
            self._whitespace = False
            result = '{&' + contents + '}'
            self._whitespace = prev
            return result
            
        if command == 'cxp':
            prev = self._whitespace
            self._whitespace = False
            contents = self(contents)
            if contents is None:
                return None
            self._whitespace = prev
            stripped = contents.strip()
            if stripped in ['.', '!', '?', ',', ';', ':']:
                return '{' + stripped + '}'
            if stripped == "'":
                return "{^'}"
            if stripped in ['-', '/']:
                return '{^' + contents + '^}'
            # Show unknown punctuation as given.
            return '{^' + contents + '^}'
        
        # unrecognized commands
        if ignore:
            return ''
        else:
            return self(contents)

    def _re_handle_eclipse_command(self, m):
        r'({[^\\][^{}]*})'
        return m.group()

    def _re_handle_text(self, m):
        r'[^{}\\\r\n]+'
        text = m.group()
        if self._whitespace:
            text = self._multiple_whitespace_pattern.sub(r'{^\1^}', text)
        return text

    def _get_matching_bracket(self, s, pos):
        if s[pos] != '{':
            return None
        end = len(s)
        depth = 1
        startpos = pos
        pos += 1
        while pos != end:
            c = s[pos]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            if depth == 0:
                break
            pos += 1
        if pos < end and s[pos] == '}':
            return pos
        return None

    def _get_command(self, s, pos):
        return self._command_pattern.match(s, pos)

    def _match_nested_command_group(self, s, pos):
        startpos = pos
        endpos = self._get_matching_bracket(s, pos)
        if endpos is None:
            return None

        command_match = self._get_command(s, startpos + 1)
        if command_match is None:
            return None

        ignore = bool(command_match.group(1))
        command = command_match.group(2)
        
        if command == 'cxconf':
            pos = command_match.end()
            last = ''
            while pos < endpos:
                if s[pos] in ['[', '|', ']']:
                    pos += 1
                    continue
                if s[pos] == '{':
                    command_match = self._get_command(s, pos + 1)
                    if command_match is None:
                        return None
                    if command_match.group(2) != 'cxc':
                        return None
                    cxc_end = self._get_matching_bracket(s, pos)
                    if cxc_end is None:
                        return None
                    last = s[command_match.end():cxc_end]
                    pos = cxc_end + 1
                    continue
                return None
            return (endpos + 1, self(last))
            
        if ignore:
            return (endpos + 1, '')
        else:
            return (endpos + 1, self(s[command_match.end():endpos]))

    def __call__(self, s):
        pos = 0
        tokens = []
        handler = self._handler
        end = len(s)
        while pos != end:
            result = handler(s, pos)
            if result is None:
                return None
            pos = result[0]
            token = result[1]
            if token is None:
                return None
            tokens.append(token)
        return ''.join(tokens)


def load_dictionary(s):
    d = {}
    converter = TranslationConverter()
    for m in DICT_ENTRY_PATTERN.finditer(s):
        steno = normalize_steno(m.group('steno'))
        translation = m.group('translation')
        converted = converter(translation)
        if converted is not None:
            d[steno] = converted
    return StenoDictionary(d)

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

import codecs
import re

from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary
# TODO: Move dictionary format somewhere more canonical than formatting.
from plover.formatting import ATOM_RE

from .rtfcre_parse import parse_rtfcre


HEADER = ("{\\rtf1\\ansi{\\*\\cxrev100}\\cxdict{\\*\\cxsystem Plover}" +
          "{\\stylesheet{\\s0 Normal;}}\r\n")

def format_translation(t):
    t = ' '.join([x.strip() for x in ATOM_RE.findall(t) if x.strip()])
    
    t = re.sub(r'{\.}', r'{\\cxp. }', t)
    t = re.sub(r'{!}', r'{\\cxp! }', t)
    t = re.sub(r'{\?}', r'{\\cxp? }', t)
    t = re.sub(r'{\,}', r'{\\cxp, }', t)
    t = re.sub(r'{:}', r'{\\cxp: }', t)
    t = re.sub(r'{;}', r'{\\cxp; }', t)
    t = re.sub(r'{\^}', r'\\cxds ', t)
    t = re.sub(r'{\^([^^}]*)}', r'\\cxds \1', t)
    t = re.sub(r'{([^^}]*)\^}', r'\1\\cxds ', t)
    t = re.sub(r'{\^([^^}]*)\^}', r'\\cxds \1\\cxds ', t)
    t = re.sub(r'{-\|}', r'\\cxfc ', t)
    t = re.sub(r'{>}', r'\\cxfls ', t)
    t = re.sub(r'{ }', r' ', t)
    t = re.sub(r'{&([^}]+)}', r'{\\cxfing \1}', t)
    t = re.sub(r'{#([^}]+)}', r'\\{#\1\\}', t)
    t = re.sub(r'{PLOVER:([a-zA-Z]+)}', r'\\{PLOVER:\1\\}', t)
    t = re.sub(r'\\"', r'"', t)

    return t


class RtfDictionary(StenoDictionary):

    def _load(self, filename):
        with open(filename, 'rb') as fp:
            text = fp.read().decode('cp1252')
        self.update(parse_rtfcre(text, normalize=normalize_steno))

    def _save(self, filename):
        with open(filename, 'wb') as fp:
            writer = codecs.getwriter('cp1252')(fp)
            writer.write(HEADER)
            for s, t in self.items():
                s = '/'.join(s)
                t = format_translation(t)
                entry = "{\\*\\cxs %s}%s\r\n" % (s, t)
                writer.write(entry)
            writer.write("}\r\n")

Spell Checking Oriented Word Lists (SCOWL)
Revision 7.1 (SVN Revision 161)
January 6, 2011
by Kevin Atkinson (kevina@gnu.org)

The SCOWL is a collection of word lists split up in various sizes, and
other categories, intended to be suitable for use in spell checkers.
However, I am sure it will have numerous other uses as well.

The latest version can be found at http://wordlist.sourceforge.net/.

The directory final/ contains the actual word lists broken up into
various sizes and categories.  The r/ directory contains Readmes from
the various sources used to create this package.

The misc/ contains a small list of taboo words, see the README file
for more info.  The speller/ directory contains scripts for creating
spelling dictionaries for Aspell and Hunspell.

The other directories contain the necessary information to recreate the
word lists from the raw data.  Unless you are interested in improving the
words lists you should not need to worry about what's here.  See the
section on recreating the words lists for more information on what's
there.

Except for the special word lists the files follow the following
naming convention:
  <spelling category>-<sub-category>.<size>
Where the spelling category is one of
  english, american, british, british_z, canadian, 
  variant_0, varaint_1, variant_2,
  british_variant_0, british_variant_1,
  canadian_variant_0, canadian_variant_1,
Sub-category is one of
  abbreviations, contractions, proper-names, upper, words
And size is one of
  10, 20, 35 (small), 40, 50 (medium), 55, 60, 70 (large), 
  80 (huge), 95 (insane)
The special word lists follow are in the following format:
  special-<description>.<size>
Where description is one of:
  roman-numerals, hacker

The perl script "mk-list" can be used to create a word list of the
desired size, it usage is:
  ./mk-list [-f] [-v#] <spelling categories> <size>
where <spelling categories> is one of the above spelling categories
(the english and special categories are automatically included as well
as all sub-categories) and <size> is the desired desired size.  The
"-v" option can be used to used to also include the appropriate
variants file up to level '#'.  The normal output will be a sorted
word list.  If you rather see what files will be included, use the
"-f" option.

When manually combining the words lists the "english" spelling
category should be used as well as one of "american", "british",
"british_z" (british with ize spelling), or "canadian".  Great care
has been taken so that that only one spelling for any particular word
is included in the main list (with some minor exceptions).  When two
variants were considered equal I randomly picked one for inclusion in
the main word list.  Unfortunately this means that my choice in how to
spell a word may not match your choice.  If this is the case you can
try including one of the "variant_0" spelling categories which
includes most variants which are considered almost equal.  The
"variant_0" spelling category corresponds mostly to American variants,
while the "british_variant_0" and "canadian_variant_0" are for British
and Canadian variants, respectively.  The "variant_1" spelling
categories include variants which are also generally considered
acceptable, and "variant_2" contains variants which are seldom used
and may now even be considered correct.  There is no
"british_variant_2" or "canadian_variant_2" spelling category since
the distinction would be almost meaningless.

The "abbreviation" category includes abbreviations and acronyms which
are not also normal words. The "contractions" category should be self
explanatory. The "upper" category includes upper case words and proper
names which are common enough to appear in a typical dictionary. The
"proper-names" category included all the additional uppercase words.
Final the "words" category contains all the normal English words.

To give you an idea of what the words in the various sizes look like
here is a sample of 25 random words found only in that size:

10: advertised agreeing artificial bucket changes closest currently finding
    implications learning liable obvious partial peace planet preparing
    produced regulations shortly tries under unnecessary vacations vast wind 

20: accomplishes addict baffles blink chapel corrections depresses dripping
    erased infant interfere launch nicking novels paranoid passport pursued
    recruitment rectifying relaxed sixteen sundry tab undergone withdraws 

35: adores affixes brisks caking conciliates decimates discretionary
    dispatches forensics glorify gridiron healed hurling kelp massacring
    necks pits placarding pyramids ratting recreates renovated sandals shirks
    subtract 

40: demoed dichotomy dilapidation disheveled ebullience estimable finagling
    hemorrhoid lazily medalists mintiest motherboards ostracism pornographers
    predilections remarries southbound steamrolled sympathizers tads tampons
    tattletale upchucked vainly viscous 

50: bootless brawler bulkhead canoeist declassifying farthings hake hectors
    helpmate hermitage humanoid kitsch mercerize pawnshops pleasingly
    retrorockets scurrilously solemnizes superficiality symbiosis tangelo
    timetabling unenviable unmoral unreconstructed 

55: beachfront bicarbonate caff campanologists execrably fab fightback
    firebricks insipidity laboriousness megawatts mirthlessly misnames
    nymphos photocell potholed psychoactive psychoanalytically schoolmarmish
    simulacra subeditors supremo sweated turbocharges yogic 

60: assayer banteringly besmeared brazer chromatin cremes deciliters
    doubtfulness enshrinement ephemerally fibular globalist gypper
    legitimatized mensch mopers oversea pantyliner paratyphoid redivide
    rehabilitative salesladies sensualists superposition univalves 

70: adactylous anticapitalist bezant bister boraginaceous civically cossacks
    cousinly curricle dekaliter grippingly grugrus gurging hermaphroditism
    levanted magnetizer nonapplicable panegyrists parametrize radomes
    refilter ruinations teths truistic uts 

80: bodikin buhrs covetiveness diarch disaccharidases drumbeater empusas
    flyings hyperexcitability hyperpolarizations janizaries overwash
    physiocrats postform postsecondary preambulate puzzlehead remixer
    snoutier tetrathlons toothdrawing triff unaffectionate wearish yawy 

95: actinophone aerobious anadenia biochemics chromatopathia ciclatouns
    gaspiest guapinol hagigah interdorsal melanotekite minnicking
    nonretrenchment overloftily oystriges peltandra retromaxillary
    subterraqueous transphysically unconfidential unvalidating upspew
    verminlike vetiveria yerth 

And here is a count on the number of in each spelling category
(american + english spelling category):

  Size   Words       Names    Running Total  %
   10    4,427          15        4,442     0.7
   20    8,122           0       12,564     1.9
   35   37,251         224       50,039     7.7
   40    6,802         503       57,344     8.8
   50   24,505      15,455       97,304    14.9
   55    6,555           0      103,859    15.9
   60   13,633         775      118,267    18.1
   70   35,507       7,747      161,521    24.8
   80  143,791      33,293      338,605    51.9
   95  227,056      86,814      652,475   100.0

(The "Words" column does not include the name count.)

Size 35 is the recommended small size, 50 the medium and 70 the large.
For spell checking I recommend using 60.  Sizes 70 and below contain
words found in most dictionaries while the 80 size contains all the
strange and unusual words people like to use in word games such as
Scrabble (TM).  While a lot of the the words in the 80 size are not
used very often, they are all generally considered valid words in the
English language.  The 95 contains just about every English word in
existence and then some.  Many of the words at the 95 level will
probably not be considered valid English words by most people.  I use
the 60 size for the English dictionary for Aspell, and I don't
recommend anyone use levels above 70 for spell checking.  Levels above
70 contain rarely used words which can hide misspellings of similar
more commonly used words.  For example the word "ort" can hide a
common typo of "or".  No one should need to use a size larger than 80,
the 95 size is labeled insane for a reason.

Accents are present on certain words such as café in iso8859-1 format.

CHANGES:

From Revision 7 to 7.1 (January 6, 2011)

  Updated to revision 5.1 of Varcon which corrected several errors.

  Fixed various problems with the variant processing which corrected a
  few more errors.

  Added several now common proper names and some other words now
  in common use.

  Include misc/ and speller/ directory which where in SVN but left
  out of the release tarball.

  Other minor fixes, including some fixes to the taboo word lists.

From Revision 6 to 7 (December 27, 2010)

  Updated to revision 5.0 of Varcon which corrected many errors,
  especially in the British and Canadian spelling categories.  Also
  added new spelling categories for the British and Canadian spelling
  variants and separated them out from the main variant_* categories.
  
  Moved Moby names lists (3897male.nam 4946fema.len 21986na.mes) to 95
  level since they contain too many errors and rare names.

  Moved frequently class 0 from Brian Kelk's Wordlist from 
  level 60 to 70, and also filter it with level 80 due to, too many
  misspellings.

  Many other minor fixes.

From Revision 5 to 6 (August 10, 2004)

  Updated to version 4.0 of the 12dicts package.

  Included the 3esl, 2of4brif, and 5desk list from the new 12dicts
  package.  The 3esl was included in the 40 size, the 2of4brif in the
  55 size and the 5desk in the 70 size.

  Removed the Ispell word list as it was a source of too many errors.
  This eliminated the 65 size.

  Removed clause 4 from the Ispell copyright with permission of Geoff
  Kuenning.

  Updated to version 4.1 of VarCon.

  Added the "british_z" spelling category which it British using the
  "ize" spelling.

From Revision 4a to 5 (January 3, 2002)

  Added variants that were not really spelling variants (such as
  forwards) back into the main list.

  Fixed a bug which caused variants of words to incorrectly appear in
  the non-variant lists.

  Moved rarely used inflections of a word into higher number lists.

  Added other inflections of a words based on the following criteria
    If the word is in the base form: only include that word.
    If the word is in a plural form: include the base word and the plural
    If the word is a verb form (other than plural):  include all verb forms
    If the word is an ad* form: include all ad* forms
    If the word is in a possessive form: also include the non-possessive

  Updated to the latest version of many of the source dictionaries.

  Removed the DEC Word List due to the questionable licence and
  because removing it will not seriously decrease the quality of SCOWL
  (there are a few less proper names).  

From Revision 4 to 4a (April 4, 2001)

  Reran the scripts on a never version of AGID (3a) which fixes a bug
  which caused some common words to be improperly marked as variants.

From Revision 3 to 4 (January 28, 2001)

  Split the variant "spelling category" up into 3 different levels.
  
  Added words in the Ispell word list at the 65 level.

  Other changes due to using more recent versions of various sources
  included a more accurate version of AGID thanks to the word of
  Alan Beale

From Revision 2 to 3 (August 18, 2000)

  Renamed special-unix-terms to special-hacker and added a large
  number of commonly used words within the hacker (not cracker)
  community.

  Added a couple more signature words including "newbie".

  Minor changes due to changes in the inflection database.

From Revision 1 to 2 (August 5, 2000)

  Moved the male and female name lists from the mwords package and the
  DEC name lists form the 50 level to the 60 level and moved Alan's
  name list from the 60 level to the 50 level.  Also added the top
  1000 male, female, and last names from the 1990 Census report to the
  50 level.  This reduced the number of names in the 50 level from
  17,000 to 7,000.

  Added a large number of Uppercase words to the 50 level.

  Properly accented the possessive form of some words.

  Minor other changes due to changes in my raw data files which have
  not been released yet.  Email if you are interested in these files.

COPYRIGHT, SOURCES, and CREDITS:

The collective work is Copyright 2000-2011 by Kevin Atkinson as well
as any of the copyrights mentioned below:

  Copyright 2000-2011 by Kevin Atkinson

  Permission to use, copy, modify, distribute and sell these word
  lists, the associated scripts, the output created from the scripts,
  and its documentation for any purpose is hereby granted without fee,
  provided that the above copyright notice appears in all copies and
  that both that copyright notice and this permission notice appear in
  supporting documentation. Kevin Atkinson makes no representations
  about the suitability of this array for any purpose. It is provided
  "as is" without express or implied warranty.

Alan Beale <biljir@pobox.com> also deserves special credit as he has,
in addition to providing the 12Dicts package and being a major
contributor to the ENABLE word list, given me an incredible amount of
feedback and created a number of special lists (those found in the
Supplement) in order to help improve the overall quality of SCOWL.

The 10 level includes the 1000 most common English words (according to
the Moby (TM) Words II [MWords] package), a subset of the 1000 most
common words on the Internet (again, according to Moby Words II), and
frequently class 16 from Brian Kelk's "UK English Wordlist
with Frequency Classification".

The MWords package was explicitly placed in the public domain:

    The Moby lexicon project is complete and has
    been place into the public domain. Use, sell,
    rework, excerpt and use in any way on any platform.

    Placing this material on internal or public servers is
    also encouraged. The compiler is not aware of any
    export restrictions so freely distribute world-wide.

    You can verify the public domain status by contacting

    Grady Ward
    3449 Martha Ct.
    Arcata, CA  95521-4884

    grady@netcom.com
    grady@northcoast.com

The "UK English Wordlist With Frequency Classification" is also in the
Public Domain:

  Date: Sat, 08 Jul 2000 20:27:21 +0100
  From: Brian Kelk <Brian.Kelk@cl.cam.ac.uk>

  > I was wondering what the copyright status of your "UK English
  > Wordlist With Frequency Classification" word list as it seems to
  > be lacking any copyright notice.

  There were many many sources in total, but any text marked
  "copyright" was avoided. Locally-written documentation was one
  source. An earlier version of the list resided in a filespace called
  PUBLIC on the University mainframe, because it was considered public
  domain.

  Date: Tue, 11 Jul 2000 19:31:34 +0100

  > So are you saying your word list is also in the public domain?

  That is the intention.

The 20 level includes frequency classes 7-15 from Brian's word list.

The 35 level includes frequency classes 2-6 and words appearing in at
least 11 of 12 dictionaries as indicated in the 12Dicts package.  All
words from the 12Dicts package have had likely inflections added via
my inflection database.

The 12Dicts package and Supplement is in the Public Domain.

The WordNet database, which was used in the creation of the
Inflections database, is under the following copyright:

  This software and database is being provided to you, the LICENSEE,
  by Princeton University under the following license.  By obtaining,
  using and/or copying this software and database, you agree that you
  have read, understood, and will comply with these terms and
  conditions.:

  Permission to use, copy, modify and distribute this software and
  database and its documentation for any purpose and without fee or
  royalty is hereby granted, provided that you agree to comply with
  the following copyright notice and statements, including the
  disclaimer, and that the same appear on ALL copies of the software,
  database and documentation, including modifications that you make
  for internal use or for distribution.

  WordNet 1.6 Copyright 1997 by Princeton University.  All rights
  reserved.

  THIS SOFTWARE AND DATABASE IS PROVIDED "AS IS" AND PRINCETON
  UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
  IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PRINCETON
  UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES OF MERCHANT-
  ABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE
  LICENSED SOFTWARE, DATABASE OR DOCUMENTATION WILL NOT INFRINGE ANY
  THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.

  The name of Princeton University or Princeton may not be used in
  advertising or publicity pertaining to distribution of the software
  and/or database.  Title to copyright in this software, database and
  any associated documentation shall at all times remain with
  Princeton University and LICENSEE agrees to preserve same.

The 40 level includes words from Alan's 3esl list found in version 4.0
of his 12dicts package.  Like his other stuff the 3esl list is also in the
public domain.

The 50 level includes Brian's frequency class 1, words words appearing
in at least 5 of 12 of the dictionaries as indicated in the 12Dicts
package, and uppercase words in at least 4 of the previous 12
dictionaries.  A decent number of proper names is also included: The
top 1000 male, female, and Last names from the 1990 Census report; a
list of names sent to me by Alan Beale; and a few names that I added
myself.  Finally a small list of abbreviations not commonly found in
other word lists is included.

The name files form the Census report is a government document which I
don't think can be copyrighted.

The file special-jargon.50 uses common.lst and word.lst from the
"Unofficial Jargon File Word Lists" which is derived from "The Jargon
File".  All of which is in the Public Domain.  This file also contain
a few extra UNIX terms which are found in the file "unix-terms" in the
special/ directory.

The 55 level includes words from Alan's 2of4brif list found in version
4.0 of his 12dicts package.  Like his other stuff the 2of4brif is also
in the public domain.

The 60 level includes all words appearing in at least 2 of the 12
dictionaries as indicated by the 12Dicts package.

The 70 level includes Brian's frequency class 0 and the 74,550 common
dictionary words from the MWords package.  The common dictionary words,
like those from the 12Dicts package, have had all likely inflections
added.  The 70 level also included the 5desk list from version 4.0 of
the 12Dics package which is the public domain.

The 80 level includes the ENABLE word list, all the lists in the
ENABLE supplement package (except for ABLE), the "UK Advanced Cryptics
Dictionary" (UKACD), the list of signature words in from YAWL package,
and the 10,196 places list from the MWords package.

The ENABLE package, mainted by M\Cooper <thegrendel@theriver.com>,
is in the Public Domain:

  The ENABLE master word list, WORD.LST, is herewith formally released
  into the Public Domain. Anyone is free to use it or distribute it in
  any manner they see fit. No fee or registration is required for its
  use nor are "contributions" solicited (if you feel you absolutely
  must contribute something for your own peace of mind, the authors of
  the ENABLE list ask that you make a donation on their behalf to your
  favorite charity). This word list is our gift to the Scrabble
  community, as an alternate to "official" word lists. Game designers
  may feel free to incorporate the WORD.LST into their games. Please
  mention the source and credit us as originators of the list. Note
  that if you, as a game designer, use the WORD.LST in your product,
  you may still copyright and protect your product, but you may *not*
  legally copyright or in any way restrict redistribution of the
  WORD.LST portion of your product. This *may* under law restrict your
  rights to restrict your users' rights, but that is only fair.

UKACD, by J Ross Beresford <ross@bryson.demon.co.uk>, is under the
following copyright:

  Copyright (c) J Ross Beresford 1993-1999. All Rights Reserved.

  The following restriction is placed on the use of this publication:
  if The UK Advanced Cryptics Dictionary is used in a software package
  or redistributed in any form, the copyright notice must be
  prominently displayed and the text of this document must be included
  verbatim.

  There are no other restrictions: I would like to see the list
  distributed as widely as possible.

The 95 level includes the 354,984 single words, 256,772 compound
words, 4,946 female names and the 3,897 male names, and 21,986 names
from the MWords package, ABLE.LST from the ENABLE Supplement, and some
additional words found in my part-of-speech database that were not
found anywhere else.

Accent information was taken from UKACD.

My VARCON package was used to create the American, British, and
Canadian word list. 

Since the original word lists used used in the VARCON package came
from the Ispell distribution they are under the Ispell copyright:

  Copyright 1993, Geoff Kuenning, Granada Hills, CA
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:

  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
  3. All modifications to the source code must be clearly marked as
     such.  Binary redistributions based on modified source code
     must be clearly marked as modified versions in the documentation
     and/or other materials provided with the distribution.
  (clause 4 removed with permission from Geoff Kuenning)
  5. The name of Geoff Kuenning may not be used to endorse or promote
     products derived from this software without specific prior
     written permission.

  THIS SOFTWARE IS PROVIDED BY GEOFF KUENNING AND CONTRIBUTORS ``AS
  IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
  FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL GEOFF
  KUENNING OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
  POSSIBILITY OF SUCH DAMAGE.

The variant word lists were created from a list of variants found in
the 12dicts supplement package as well as a list of variants I created
myself.

The Readmes for the various packages used can be found in the
appropriate directory under the r/ directory.

FUTURE PLANS:

The process of "sort"s, "comm"s, and Perl scripts to combine the many
word lists and separate out the variant information is inexact and
error prone.  The whole things needs to be rewritten to deal with
words in terms of lemmas.  When the exact lemma is not known a best
guess should be made.  I'm not sure what form this should be in.  I
originally thought this should be some sort of database, but maybe I
should just slurp all that data into memory and process it in one
giant perl script.  With the amount of memory available these days (at
least 2 GB, often 4 GB or more) this should not really be a problem.

In addition, there is a very nice frequency analyze of the BNC corpus
done by Adam Kilgarriff.  Unlike Brain's word lists the BNC lists
include part of speech information.  I plan on somehow using these
lists as Adam Kilgarriff has given me the OK to use it in SCOWL.
These lists will greatly reduce the problem of inflected forms of a
word appearing at different levels due to the part-of-speech
information.

There is frequency information for some other corpus such as COCA
(Corpus of Contemporary American English) and ANS (American National
Corpus) which I might also be able to use.  The formal will require
permission, and the latter is of questionable quality.

RECREATING THE WORD LISTS:

In order to recreate the word lists you need a modern version of Perl,
bash, the traditional set of shell utilities, a system that supports
symbolic links, and quite possibly GNU Make.  The easiest way to
recreate the word lists is to checkout SVN revision 161 (or tag
scowl-7.1) and simply type "make" (see http://wordlist.sourceforge.net).
You can try to download all the pieces manually, but you may not get
the same result since the latest version of some parts used to create
SCOWL may not have been released yet.

The src/ directory contains the numerous scripts used in the creation
of the final product. 

The r/ directory contains the raw data used to create the final
product.  If you checkout from SVN this directory should be populated
automatically for you.  If you insist on doing it the hard way see the
README file in the r/ directory for more information.

The l/ directory contains symbolic links used by the actual scripts.

Finally, the working/ directory is where all the intermittent files go
that are not specific to one source.

Quick Start
===========

Installation
------------

The latest release of <span>*Plover*</span> can be downloaded from
<https://launchpad.net/plover> as a compressed <span>`.tar.gz`</span>
archive that must be extracted. Among the extracted files will be a
README.txt file. Follow the directions in this file for installing and
running <span>*Plover*</span>.

Starting the Program
--------------------

Once installed, <span>*Plover*</span> can be run from either the
application menu or from a <span>[terminal
window](https://help.ubuntu.com/community/UsingTheTerminal)</span> (<span>`plover`</span>
and then <span>`ENTER`</span>). If a stenotype machine other than the
default is used, set the machine type in the configuration dialog.

Configuration {#config}
-------------

<span>*Plover*</span> comes with a default configuration that should
work for most setups that use a keyboard as the stenotype machine.
<span>*Plover*</span> can be configured by clicking the
<span>`Configure...`</span> button. Within the configuration dialog, the
user can select which stenotype machine to use, which dictionary file to
use, whether or not strokes and translations should be logged to a file,
and whether or not <span>*Plover*</span> should immediately start
translating when the program is started. <span>*Plover*</span> will need
to be restarted before any configuration changes take effect.

Stenography Dictionary
======================

At the core of stenography is a dictionary that translates stroke
combinations into words and phrases. The words and phrases can be
English, another language, or a nonsense string of characters. The words
and phrases can also be commands and special keys other than printable
characters.

Dictionary Format
-----------------

<span>*Plover*</span> expects the stenography dictionary file to be in
JSON format and each dictionary entry within the file to be in a
specific variant of RTF/CRE format.

### Single-stroke Entries

A simple dictionary entry looks like:

<span>`STROKE: word or phrase,`</span>

For example:

-   <span>`TKO: do,`</span>

-   <span>`K: can,`</span>

-   <span>`KWRORPBL: I don’t remember,`</span>

-   <span>`PHAS: mas,`</span>

### Multiple-stroke Entries

A dictionary entry for more than one stroke looks like:

<span>`STROKE1/STROKE2/STROKE3: another word or phrase,`</span>

-   <span>`SEUPB/OPB/PHOUS: synonymous,`</span>

-   <span>`TKE/TPER: defer,`</span>

-   <span>`TOEPBD/SRA*EU: tend to have a,`</span>

-   <span>`KWREUP/KWREU/KAOEU/KWRAEU: yippee ki-yay,`</span>

-   <span>`PEPB/SAR: pensar,`</span>

### Meta Commands

Meta commands are dictionary entries surrounded by { and }, like:

<span>`STROKE1/STROKE2: { opolis},`</span>

which means append “opolis” to the previous word without inserting a
space.

Meta commands and regular text can be mixed, like:

<span>`STROKE1/STROKE2: {.}Thus, we can see that,`</span>

which means append a period and the number of spaces after a period and
the text “Thus, we can see that”.

Spaces between meta commands and regular text don’t count, so the
previous example is the same as:

<span>`STROKE1/STROKE2: {.} Thus, we can see that,`</span>

Furthermore, since the <span>{.}</span> meta command will also
capitalize the next word, the previous example is also the same as:

<span>`STROKE1/STROKE2: {.} thus, we can see that,`</span>

There can be more than one meta command in a translation, like:

<span>`STROKE1/STROKE2: "{,}like{,}`</span>"

Since <span>`"`</span>, <span>``{</span>, and <span>`}`</span> are all
special dictionary format characters, the character sequences
<span>`\backslash"`</span>, <span>``$\backslash${</span>, and
<span>`\backslash}`</span>, should be used within a translation, like:

<span>`STROKE1/STROKE2: { .\backslash" }{-},`</span>

which will append ." and a space to the previous word and then
capitalize the next word.

<span>*Plover*</span> supports the following meta commands:

-   Sentence stops: <span>{.}</span>, <span>{!}</span>, <span>{?}</span>
    all end a sentence with the corresponding punctuation, insert a
    space and capitalize the next letter.

-   Sentence breaks: <span>{,}</span>, <span>{:}</span>,
    <span>{;}</span> all break a sentence with the
    corresponding punctuation.

-   Simple suffixes: <span>{ ed}</span>, <span>{ ing}</span>, <span>{
    er}</span>, <span>{ s}</span> applies basic orthographic rules to
    append the corresponding prefix to the most recent word to form the
    past tense, present progressive, noun, or plural, respectively.

-   Capitalize: <span>{-}</span> capitalizes the next letter.

-   Glue flag: <span>{&X}</span> will connect the string X without a
    space to any adjacent (previous or following) strings that also have
    glue flags.

-   Attach flag: <span>{ X}</span>, <span>{X }</span>, <span>{ X
    }</span> will connect the string X without a space to the previous,
    next, or both previous and next, respectively, words, unless X is
    one of the simple suffixes (ed, ing, er, s), in which case the
    simple suffix rules take precedence.

-   <span>*Plover*</span> controls: <span>{PLOVER:X}</span> will control
    the state of the <span>*Plover*</span> program itself, where X is
    one of <span>`SUSPEND`</span>, <span>`RESUME`</span>,
    <span>`TOGGLE`</span>, <span>`CONFIGURE`</span>,
    <span>`FOCUS`</span>, or <span>`QUIT`</span>.

-   Key combinations: <span>{\#X}</span> will execute the key
    combination described by X. See below for details.

### Arbitrary Key Combinations

Meta commands of the form <span>{\#X}</span> are interpreted as a
sequence of keyboard keys pressed and released in sequence and/or
simultaneously. Serial key presses are separated by a single space.
Simultaneous key presses are denoted by parentheses surrounding keys
pressed while another key is held down. For example:

<span>`Alt_L(Tab)`</span>

will emulate the action of holding down the left Alt key while pressing
and releasing the Tab key and then releasing the left Alt key.
Parentheses can be nested, as in:

<span>`Control_L(Shift_L(minus minus minus)`</span>

which would emulate holding down the left Control key, then holding down
the left Shift key, and then pressing the minus (-) key three times
before releasing the left Shift and then the left Control keys.

Below is the list of all legal keys that can be used to form key
combination commands.

-   0 1 2 3 4 5 6 7 8 9

-   a b c d e f g h i j k l m n o p q r s t u v w x y z

-   A B C D E F G H I J K L M N O P Q R S T U V W X Y Z

-   Alt\_L Alt\_R Control\_L Control\_R Hyper\_L Hyper\_R Meta\_L
    Meta\_R Shift\_L Shift\_R Super\_L Super\_R

-   Caps\_Lock Num\_Lock Scroll\_Lock Shift\_Lock

-   Return Tab BackSpace Delete Escape Break Insert Pause Print Sys\_Req

-   Up Down Left Right Page\_Up Page\_Down Home End

-   F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 F13 F14 F15 F16 F17 F18 F19
    F20 F21 F22 F23 F24 F25 F26 F27 F28 F29 F30 F31 F32 F33 F34 F35

-   L1 L2 L3 L4 L5 L6 L7 L8 L9 L10

-   R1 R2 R3 R4 R5 R6 R7 R8 R9 R10 R11 R12 R13 R14 R15

-   KP\_0 KP\_1 KP\_2 KP\_3 KP\_4 KP\_5 KP\_6 KP\_7 KP\_8 KP\_9 KP\_Add
    KP\_Begin KP\_Decimal KP\_Delete KP\_Divide KP\_Down KP\_End
    KP\_Enter KP\_Equal KP\_F1 KP\_F2 KP\_F3 KP\_F4 KP\_Home KP\_Insert
    KP\_Left KP\_Multiply KP\_Next KP\_Page\_Down KP\_Page\_Up KP\_Prior
    KP\_Right KP\_Separator KP\_Space KP\_Subtract KP\_Tab KP\_Up

-   ampersand apostrophe asciitilde asterisk at backslash braceleft
    braceright bracketleft bracketright colon comma division dollar
    equal exclam greater hyphen less minus multiply numbersign parenleft
    parenright percent period plus question quotedbl quoteleft
    quoteright semicolon slash space underscore

-   AE Aacute Acircumflex Adiaeresis Agrave Aring Atilde Ccedilla Eacute
    Ecircumflex Ediaeresis Egrave Eth ETH Iacute Icircumflex Idiaeresis
    Igrave Ntilde Oacute Ocircumflex Odiaeresis Ograve Ooblique Otilde
    THORN Thorn Uacute Ucircumflex Udiaeresis Ugrave Yacute

-   ae aacute acircumflex acute adiaeresis agrave aring atilde ccedilla
    eacute ecircumflex ediaeresis egrave eth iacute icircumflex
    idiaeresis igrave ntilde oacute ocircumflex odiaeresis ograve oslash
    otilde thorn uacute ucircumflex udiaeresis ugrave yacute ydiaeresis

-   cedilla diaeresis grave asciicircum bar brokenbar cent copyright
    currency degree exclamdown guillemotleft guillemotright macron
    masculine mu nobreakspace notsign onehalf onequarter onesuperior
    ordfeminine paragraph periodcentered plusminus questiondown
    registered script\_switch section ssharp sterling threequarters
    threesuperior twosuperior yen

-   Begin Cancel Clear Execute Find Help Linefeed Menu Mode\_switch
    Multi\_key MultipleCandidate Next PreviousCandidate Prior Redo
    Select SingleCandidate Undo

-   Eisu\_Shift Eisu\_toggle Hankaku Henkan Henkan\_Mode Hiragana
    Hiragana\_Katakana Kana\_Lock Kana\_Shift Kanji Katakana Mae\_Koho
    Massyo Muhenkan Romaji Touroku Zen\_Koho Zenkaku Zenkaku\_Hankaku

Editing the Dictionary
----------------------

To edit the dictionary file, issue the following command in a
<span>[terminal
window](https://help.ubuntu.com/community/UsingTheTerminal)</span>:

    gedit $HOME/.config/dict.json

or a comparable command with the location of whatever dictionary file
<span>*Plover*</span>  is configured to use. In case of a character
encoding error in <span>`gedit`</span>, do the following:

1.  Click the character encoding drop-down list.

2.  Select Add or Remove...

3.  Select Western ISO-8859-1, also known as latin-1.

4.  Click the Add button.

5.  Click the OK button.

6.  Select ISO-8859-1 from the character encoding drop-down list.

7.  Click the Retry button.

Further Resources
=================

Other than this document, there are several resources for getting help
with <span>*Plover*</span>:

-   mailing list: <http://groups.google.com/group/ploversteno>

-   blog: <http://plover.stenoknight.com>

-   IRC channel: <span>`#plover`</span> on
    <span>`irc.freenode.net`</span> or\
    <http://webchat.freenode.net/?channels=#plover>

-   download and development: <http://launchpad.net/plover>

-   general information: <http://stenoknight.com/plover>



Stenography for Beginners
=========================

.. note::
    This page is for general users who are new to steno. If you're a steno
    professional, read :doc:`pro_steno`.

What is stenography?
--------------------

Stenography is a form of shorthand writing/typing, usually done on a special
machine (although with Plover, you can use computer keyboard that has
`n-key rollover <https://en.wikipedia.org/wiki/Rollover_(key)>`_). It was
invented in the early 1900s.

Real-time machine stenography is a code translation system that lets users
enter words and syllables by pressing multiple keys simultaneously in a chord,
which is then instantly translated into English text.

This makes steno the fastest and most accurate text entry method currently
available.

=========================   =============
Method                      Typical Speed
=========================   =============
Handwriting                   30 wpm
Average Typist                40 wpm
Fast Typist                  120 wpm
Typing World Record          200 wpm
Voice Writer                 180 wpm
Average Speech               200 wpm
Amateur Stenographer         160 wpm
Professional Stenographer    225 wpm
Steno World Record           360 wpm
=========================   =============

In the first year of steno school, many students learn to exceed 100
words per minute. By comparison, top qwerty typists can do 120wpm, top Dvorak
typists around 140wpm, and voice writers dictating to voice recognition software
around 180wpm. But experienced stenographers can enter text at up to 300wpm
(the world record is actually 360, but that's an outlier). Conceivably, with
practice, amateur steno users could reach 160-200 words per minute.

How does it work?
-----------------

The main difference between typing and stenography
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. youtube:: UtQzTUEuPWo

Most likely, you are using a QWERTY or Dvorak keyboard layout to type everything
out character by character. If you ever practiced piano, it might be helpful to
liken them to certain piano pieces common in a pianist's repertoire. The
"typewriter-style" systems (QWERTY, Dvorak, etc.) are like Chopin's Fantasie Impromptu:

.. youtube:: tvm2ZsRv3C8

Notice how this piece—like typing—is mainly runs of single fingers. When you
learn and practice this piece, you often do many finger exercises to strengthen
certain fingers to increase your speed.

However, Plover, and other steno systems, use keyboard "chords" to type
syllables, words, or entire phrases. You press keys, and lift off, rather than
pressing down individual keys one after the other.

    When your fingers are in position, press them all down together, and
    release them. Out comes the word 'tap'! You've just tapped your first word
    in steno! Notice that it doesn't really matter that all the keys go down
    absolutely simultaneously. The only thing Plover cares about is that there's
    one moment in time when all three keys are down together.

    (From |learnplover|_)

.. |learnplover| replace:: *Learn Plover!*
.. _learnplover: https://sites.google.com/site/learnplover/

Plover - and all steno systems - express words primarily as groups of sounds
rather than groups of letters of the alphabet.

"Steno-style" systems (NYCI, StenEd, Phoenix, etc.) are like Rachmaninoff's
Prelude in G Minor:

.. youtube:: 4QB7ugJnHgs

Unlike the Chopin, this piece is almost entirely chorded. When learning a
piece like this, you learn how to block your chords. So your approach to
learning steno may be completely different than learning a different keyboard
layout, since it's a completely different system.

Why learn steno? And how?
-------------------------

Mirabai Knight has broken the answer to the first question into six parts:

  1.  `How to Speak With Your Fingers <http://stenoknight.com/SpeakFingers.html>`_:
      for people who can't use their voice to speak but want to communicate in
      real-time using a steno-enabled text to speech device.

  2.  `Writing and Coding <http://stenoknight.com/WritingCoding.html>`_:
      for people whose fluency of thought depends on ease and efficiency of
      text input.

  3.  `The Ergonomic Argument <http://stenoknight.com/ErgonomicArgument.html>`_:
      for people who want to avoid wasted effort and repetitive stress injuries.

  4.  `Mobile and Wearable Computing <http://stenoknight.com/MobileWearable.html>`_:
      for people who want to input text and control their computers while
      walking around, with a minimum of dorkitude.

  5.  `Raw Speed <http://stenoknight.com/RawSpeed.html>`_:
      for people who have to be the fastest, no matter what.

  6.  `CART, Court, and Captioning <http://stenoknight.com/CARTCourtCaptioning.html>`_:
      for people who want to provide live verbatim transcription professionally.

See :doc:`learning_steno` for a list of resources for learning stenography.

Why isn't steno more popular than QWERTY?
-----------------------------------------

There are a number of possible reasons:

  * Stenography was copyrighted for many decades, which limited the amount of
    competition in the marketplace.
  * The vendors decided to focus on high value products in market sectors where
    organizations would be willing to pay higher prices.
  * It takes longer to learn how to write with steno than it does learning how
    to type.
  * Plover software, and suitable low cost hardware, didn't exist until recently.

What is Plover?
---------------

Plover is the world's first free, open-source stenography program. It is a small
Python application that you run in the background. It acts as a translator to
read steno movements and then emulate keystrokes, so the programs you use can't
tell that you are using steno.

Plover is available on Windows, Mac and Linux.

How is Plover different from commercial steno programs?
-------------------------------------------------------

Well, first off, it's free. Free to distribute, free to modify. No dongles, no
upgrade fees, no constraints. That's already a $4,000 difference.

To the developer's knowledge, it's also the only steno software that works on a
buffer-based system rather than a timer-based system, and that has direct access
to the OS rather than filtering everything into a steno-specific word processor.
This means it's lightweight, powerful, and doesn't require a 1.5-second wait
time between when a stroke is entered and when the translation appears in an
external program. In Plover, the translation appears instantly, and the
software isn't cluttered up with file managers, printer handlers, and other
court-reporting flimflam that an amateur stenographer will never use. Instead,
it's a direct conduit between the steno keyboard and the OS. Plover can do
everything a QWERTY keyboard can do – but much, much faster.

What does Plover look like in action?
-------------------------------------

Here is a video of Ted Morin using Plover to write some simple JavaScript code:

.. youtube:: RBBiri3CD6w

Here is a demonstration of Plover with a QWERTY Keyboard. It shows the keys
pressed along with their resulting output. See
`Mirabai's blog post <http://plover.stenoknight.com/2011/10/split-screen-demonstration.html>`__

.. youtube:: JXQQzW99cAI

Here's a video of Mirabai kicking someone's butt in
`TypeRacer <http://play.typeracer.com/>`_, an online typing game that lets
people race against each other by hammering out random snippets of text at high
velocities:

.. youtube:: jkUyg_uoidY

And here's a demonstration of Plover with eSpeak, a free text-to-speech engine,
which can be a way to talk at a normal conversational pace by people who don't
use their voices to speak, as discussed in
`How to Speak With your Fingers <http://stenoknight.com/SpeakFingers.html>`__.

.. youtube:: K3MYFT6VZk8

Why was Plover written?
-----------------------

A professional stenographer, forced to buy proprietary (and DRM-riddled) steno
software for $4,000 plus an annual $700 upgrade fee after shelling out for a
$3,000 steno machine, looked around and saw that most of the people who made
their living and their free time putting text up on a screen were crawling
along at around 60 words per minute because they were using QWERTY instead of
steno. She realized that the only way to spread the wonders of high speed
efficient text entry to the geeks, hackers, writers, and internet addicts who
desperately needed it was to make the software free and the hardware cost less
than $60. She found a Python programmer who was also a hardware maven, and they
both got down to work. Eleven months later, Plover was ready for prime time.

What hardware is needed to use Plover?
--------------------------------------

See the :doc:`hardware_guide`.

What can Plover do right now?
-----------------------------

Plover can write properly capitalized and punctuated text into any window as if
it were an ordinary keyboard. It can send command strokes such as Enter or
Escape, giving it complete equivalence to the Qwerty keyboard. It's also a
robust and convenient text entry system, suitable for writing, coding, chatting,
and kicking people's butts at online typing games.

What Plover cannot do right now
-------------------------------

Sticky Metakeys
^^^^^^^^^^^^^^^

Plover lacks arbitrarily stackable metakeys. You can explicitly define a
metakey+key combination in the dictionary (and there is a dictionary for general
shortcuts such as ``Control-C``), but you can't map a stroke to, say,
``Control`` and then be able to simulate holding it down while choosing another
key in realtime to be activated along with it.

Transcript management and workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plover is not court reporting (CAT) software, and there are no plans to make it
into CAT replacement software. It has no transcript preparation utilities of
any kind. For example: document approval and delivery workflow, document encryption, or file management.

For more information, see: :ref:`cat_software_business`

Non-English languages
---------------------

The Plover software is currently designed for the English steno keyboard layout,
but it is possible to customize the steno layout. Some unofficial work has been
done by users on creating
`French <https://github.com/azizyemloul/plover-france>`__,
`German <https://groups.google.com/d/msg/ploversteno/MYNlSMD68Qc/Byyw9T8ZCQAJ>`__
and `Portuguese <http://openstenoblog.blogspot.co.uk/2015/04/my-experience-in-open-source.html>`__
versions, by forking the software from the repository to create versions for
other language layouts.

There has been some work on developing free-of-charge steno dictionaries for
other languages (for example,
`French <https://github.com/azizyemloul/plover-france-dict>`__,
German (`1 <https://groups.google.com/d/msg/ploversteno/MYNlSMD68Qc/Byyw9T8ZCQAJ>`__ and
`2 <http://stanographer.com/steno-hell-german/>`__),
`Portuguese <http://openstenoblog.blogspot.co.uk/2015/04/my-experience-in-open-source.html>`__
and Spanish), which could be used while retaining the English steno keyboard layout.

Plover can also work with exported dictionaries from commercial stenography applications such as Eclipse, ProCAT and Case CATalyst.

More information:

  * :doc:`dictionary_format`

Is an NKRO keyboard as fast as a steno machine?
-----------------------------------------------

No. It's definitely clunkier and squishier than a genuine lever-based steno
machine, and a certain amount of accuracy and speed is necessarily sacrificed
because of that. It's also somewhat more fatiguing, because it requires more
force to press the keys and their travel depth is deeper than most modern steno
machines.

However, it's perfectly possible for a trained stenographer to reach speeds of
220wpm or higher using something like a Sidewinder X4, especially if they have
the optional laser-cut steno keytoppers
(`$20 from the Plover store <http://plover.deco-craft.com/shop/view_product/Laser_Cut_Steno_Keys_Kit?n=2910988>`__):

.. image:: https://camo.githubusercontent.com/db6a66a25444e0742883afca7aa765477996ca798010d7a4ef97581e4c8b4e6d/687474703a2f2f706c6f7665722e6465636f2d63726166742e636f6d2f737063696d616765732f323136323137382f383134383135382f312f312f4343434343432f70726f642e6a70673f623d313039333432353826763d31343537393634343836

Various steno enthusiasts are making and selling machines designed for use with
Plover. These typically use keys that require less actuation force than the keys
found on a QWERTY keyboard, and they have the steno "22 key" ortholinear layout.
They usually cost more than an NKRO qwerty keyboard and less than a professional
steno machine. See :ref:`dedicated_machines`.

How many people currently use Plover?
-------------------------------------

Hard to say, since people are free to download and distribute the software as
much as they want without asking permission. However, the Plover Google Group
currently has 578 members.

Who's responsible for Plover's development?
-------------------------------------------

Plover was originally created by
`Mirabai Knight <http://www.blogger.com/profile/16494847224950297255>`__ and
`Joshua Harlan Lifton <http://launchpad.net/~joshua-harlan-lifton>`__, and is
the software arm of the
`Open Steno Project <http://openstenoproject.org/>`__, an umbrella organization
for open source steno tools. The current lead developer is Theodore (Ted) Morin.

Why "Plover"?
-------------

The short answer is that it's a two-syllable, six-letter word that can be
written in a single stroke on a steno machine. The longer answer is
`here <http://plover.stenoknight.com/2010/03/why-plover.html>`__.

Does the Plover Project accept donations?
-----------------------------------------

Absolutely. Contributions of money, code, testing, documentation, publicity, or
TypeRacer cannon fodder are
`gratefully accepted <http://stenoknight.com/plover/donatepage.html>`__.

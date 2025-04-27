# Designing Steno Systems

*Special thanks for Kaoffie for contributing this guide.*

## What goes into a Stenographic System?

There are three things that go into a stenographic system for it to work: the layout, the theory, and the dictionary. You will have to plan and create all three of these before you can use your system to work.

- **The layout**: What the shape of the board is, where the keys go on the board, and what the role of each key is (the sounds or letters each key represents).

- **The Theory**: The rules that determine how words or phrases are stroked on the board. The English layout, for example, has many theories that use the same layout, including the default Plover theory.

- **The Dictionary**: The dictionary files that map chords to words, phrases and symbols. You won't need to create a full dictionary for the system to work, just a small one with all the basic words. Some systems (orthographic systems) don't require traditional dictionaries with one-to-one mappings, but rather a set of rules written in code that can convert the strokes into words without individually defined dictionary entries. 


## The Design Process

The design process of a stenographic system usually goes like this: 

- [Selecting a type of stenographic system](system-dev/steno-system)
- [Selecting a board layout](system-dev/board-layout)
- [Arranging the keys](system-dev/key-arrangement)
- [Testing the layout](system-dev/layout-test)
- [Implementing the system and creating the dictionary](system-dev/system)

Before designing your system, it is important to know what the goals of your system are - what speeds you would like to reach, what type of input device you'd like to cater to, what the intended users of the system would be, and so on. In this guide, we'll be designing a new example system together with these goals so that you may better understand what the process is like:

- **English steno system.** The system would be used for inputting the English language.
- **One-handed.** The system would only have keys for the left hand.
- **Not realtime capable, but faster than one-handed typing.** We're not aiming for speeds comparable with two-handed steno, but something that's fast enough to beat one-handed keyboard layouts such as left-handed Dvorak. 

It would be a good idea for you to also list your goals like this too! 

```{toctree}
:hidden:
:maxdepth: 2

system-dev/steno-system
system-dev/board-layout
system-dev/key-arrangement
system-dev/layout-test
system-dev/system
```

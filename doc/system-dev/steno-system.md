# Types of Stenographic Systems

The first thing you'll have to decide when designing a stenographic system for your language is what kind of system you would like to design. This is highly dependant on the phonology and the orthography of the language that you're designing for, and the intended purpose of the system.


## Comparing Stenographic Systems

### Phonetic

Phonetic systems are mainly based on the phonetics of the language rather than its spelling; many phonetic systems do incorporate spelling-based entries in their theories, but most entries are based on how things are pronounced, rather than how they are written.

Phonetic systems are generally suitable for languages with inconsistent spelling rules (such as English) or spelling rules that have diverged from the actual pronunciation (such as French), or languages such as Chinese or Japanese that use logographic/hybrid scripts.

Phonetic systems rely on dictionaries much more than orthographic systems; expect to generate a dictionary for all the basic words in the system before it can be usable.

<div align="center"><img src="https://github.com/Kaoffie/steno_diags/blob/master/converted/en-0.png?raw=true" width="500"></div>

Phonetic systems are generally not concerned with being able to write every single common letter combination on both hands, especially if they're irrelevant to the pronunciation of a word. For instance, in the English layout as shown above, most theories don't include a way to write the letter Q on the right side (despite there being syllables that end with Q in the language, such as "cheque"), since what we're concerned with is the pronunciation, and the right hand K sound (made with the chord `BG`) is good enough. 

Phonetic systems are great for dictation speed: when transcribing audio, being able to write directly using pronunciation rather than spelling can reduce the cognitive load since there isn't the extra step of converting the audio into spelling. 

The greatest weakness of phonetic systems are homophones - when words are spelled differently but pronounced the same (For example, "their"/"they're"/"there"). When designing a phonetic system, you will have to decide on a method to disambiguate between these words effectively, and many of these methods might require additional memorization. 

### Orthographic

For languages where the orthography is consistent with the pronunciation, we can opt for an orthographic system where chords are derived entirely based on the spelling of words. This means that the system can work without a dictionary - so long as there are well defined rules for spelling letters, you would theoretically be able to type every single word. With the right system design, an orthographic system may also be capable of writing multiple languages with similar orthography, such as language families that share the same script. 

<div align="center"><img src="https://github.com/Kaoffie/steno_diags/blob/master/converted/zz-velo.png?raw=true" width="500"></div>

The velotype system is a common orthographic system designed for Dutch and many other European languages. It is able to write many different languages because it's entirely based on spelling, unlike a phonetic system designed for the phonology of a single language. For example, the word "fiction" would be written as `FIC/TION` rather than something like `FIK/SHUN` in a phonetic system. 

Orthographic systems frequently use dictionaries for briefs, or abbreviations of entire words or phrases that can't otherwise be written with the orthographic rules. 


## Picking a system

It is important to note that languages that have inconsistent orthographies don't have to always be written using phonetic systems, and languages with consistent orthographies can also benefit from a phonetic system. More often than not, you would be able to pick either system type depending on the goals you have. 

### Things to consider

- **For languages with fixed syllable structure**, such as Korean or Mandarin Chinese, the system you create will most likely be neatly divided into different sectors, each for a different section of the syllable. For instance, in Korean, where each syllable consists of an initial, medial, and a final, steno systems might have a left bank for the initial, a thumb cluster for the medial, and a right bank for the final, allowing users to write every possible syllable with a single stroke. 

- **For languages that use logographic scripts**, such as kanji, you'll have to create a system to disambiguate between different characters, especially those that have the same pronunciations. It is okay to decide on the details of this disambiguation system later, but it may influence your decision when deciding on a system type. 

- **For tonal languages**, such as Thai or Cantonese, you will have to choose how to incorporate tones into the system too. Some steno systems, such as Yawei Mandarin, choose not to use tone at all, while other steno systems like the Vietnamese steno systems choose to include a section on the steno board for specifying the tone of each syllable.

- **For languages that use Abjads**, such as Hebrew or Arabic, where vowels are optional, how important you view the ability to input vowels will also influence your decision. Think about how you would like to treat vowels, whether they would be useful in the input system even if the output doesn't include them, and whether you would like an input mode that does include the vowels.

### Bad system ideas

- **Category-based system**: a system that splits the vocabulary in the language into different categories and inputs them accordingly, rather than their spelling or pronunciation. This adds a lot of cognitive load to the system due to the extra step of figuring out which category a word belongs to, and forces the author to make a lot of arbitrary decisions for words that don't fall neatly into the different categories.

- **Context-based disambiguation**: a system where many words are assigned the same stroke and are differentiated based on context, much like autocorrect. This makes the output of the system unpredictable for the steno user; while it used to work for stenographers that used paper tape and human translations, it is generally a bad idea for modern steno systems.

- **Orderless system**: a system where the left and right sides of the board do not necessarily correspond to different parts of a word or syllable; rather, words are pieced together from letters on the steno board with no regard to the positions of the letters. These systems are usually bad at disambiguating between anagrams, or words that use the same letters (such as "rat"/"tar")


## Example

In our one-handed English steno example, here is what we'll be going with:

- **Phonetic**: There are too many letters to squeeze into one hand for us to go with an orthographic system. If we were to include letters such as Q or C in an orthographic system, that would force us to include more keys for these extra letters even though their sounds can already be represented by K or S, which will make the system hard to use with one hand.

- **Orthography sometimes used for disambiguation**: English contains a lot of words like "beet" versus "beat" that are pronounced the same, hence we'll have to resort to using orthography/spelling to tell them apart. 

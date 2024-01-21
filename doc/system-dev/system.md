# Implementing the System

For more details on creating a system plugin on Plover, check out [this guide](../plugin-dev/systems).

## Orthography

Some systems, including English stenotype, includes orthography rules. These are spelling rules that are encoded in the system outside of the dictionary to ensure that suffixes are attached correctly. Here are some of the orthography rules in English:

- `sh` + `s` = `shes` (publish, publishes)
- `ie` + `ing` = `ying` (lie, lying)

There are a few things to take note when making these orthography rules:

- **Don't make an orthography rule just for a single word.** If your rule only applies to a single word, it's better to include it in the dictionary instead. For instance, the suffix `{^nance}`, when attached to the word "maintain", gives "maintenance". We don't need to include the orthography rule `ain` + `nance` = `enance`; simply including it in the dictionary is good enough.
- **Don't make your orthography rule too general.** It is much better to write orthography rules that are more specific. For instance in English, instead of writing the rule `y` + `i` = `i`, it is far better to write rules for individual cases, such as `y` + `ial` = `ial`, `y` + `ical` = `ical` and so on. This prevents rules from changing words that they shouldn't change.
- **Orthography rules can have exceptions.** If there are only a few exceptions, you can include them in the dictionary. If there are too many exceptions, consider making the rule more specific if possible to reduce the number of exceptions.
- **Orthography rules only apply to `{^suffix}`, not `{^}suffix`.** It might help to know that you can explicitly define suffixes in your dictionary that are not affected by orthography rules.


## Generating the Dictionary

If you chose to make a phonetic system, then you'll have to generate a basic dictionary before the system is usable. The process of dictionary-building can be slow, especially if you choose to refine your dictionary manually over the span of several months. You may also choose to generate your dictionary automatically, and there are many tools to help you with that. Here are some tools to help you with making a dictionary:

- [**Plover Dictionary Builder**](https://github.com/morinted/plover_dictionary_builder): A dictionary builder plugin that allows you to add dictionary entries for multiple words in one go.
- [**Plovary**](https://github.com/42triangles/plovary): A dictionary generation tool written in Python.


If you are making an orthographic system, then you'll find [Python Dictionaries](https://github.com/benoit-pierre/plover_python_dictionary) useful. Python dictionaries allow you to programmatically translate input strokes into words without explicitly defining the translation of every possible stroke like in a traditional dictionary.

Here are some tips for generating a dictionary:

- **It is not always a good idea to blindly include as many words as possible.** Often, when system designers try to include as many words as they possibly can in the dictionary, they might end up including rare words in the dictionary that interfere with common words. For instance, including the word "Tob" might prevent you from including an easy way to write "to be". In such cases, you might choose to add a disambiguation key to the rare word entry (such as the asterisk key on the English layout), or make it such that the word cannot be written normally unless the user is intentionally trying to write it.
- **You might want to include word stems in your dictionary, even if they're not actual words by themselves.**
- **Try to categorize your dictionary.** Separate the words from the symbols and phrases, and misstrokes from the correct strokes. This will help you and potential learners tremendously and will ensure that you have a clean and maintainable dictionary.

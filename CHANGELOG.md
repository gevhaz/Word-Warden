# Changelog

## [Unreleased]

- Change `spellcheck.py` to take one or more files as positional argument,
  rather than a glob expression as a single string.

## [0.2.0] - 2024-01-17

- Created a versioning strategy that ensures the version of the Action someone
  uses corresponds with the content of the repository at that version. The
  Action has been adapted to align with this strategy.
- Change name of personal dictionary from `wordlist.txt` to
  `project-dictionary.txt`.
- Print a list of all suspected misspelled files at the end of the Action
  output, as a summary.
- Checkout both Word Warden and the repository that will be checked for spelling
  errors in different subdirectories to make sure all necessary files are
  available.

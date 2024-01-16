# Word Warden

**Word Warden** is a GitHub action that spellchecks markdown or other files in
your repository. It uses `aspell` under the hood, checking your text against a
dictionary for the language of your chose, plus a personal dictionary with your
own approved words.

## Usage

Simply include the action `gevhaz/word-warden` in your job like so:

```yaml
jobs:
  spellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gevhaz/word-warden
```

If it finds any words that you consider false positives, add them to the file
`.github/data/wordlist.txt` in your repository (or any other dictionary you
specify with the `files` option). Make sure to add:

```text
personal_ws-1.1 en 1000 utf-8
```

as the first line in the file. Replace `en` with the language code of your
language if it's not English.

## Optional input arguments

By default,the action checks all markdown files in your repository (that have
the `.md` extension) but you can also select any other files by specifying the
`files` option. Glob expressions may be used.

The default language is American English (`en_US`). Set any other language that
`aspell` accepts with the `language` argument to the Action.

By default the action looks for your personal dictionary at
`.github/data/wordlist.txt` and if you don't have one there, it acts as if you
had an empty one. Specify any other location for you dictionary with the
`dictionary` key.

Here is an example with all options used:

```yaml
jobs:
  spellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gevhaz/word-warden
        with:
          language: en_IN
          dictionary: ./words.txt
          files: README.md
```

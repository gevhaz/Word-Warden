# Word Warden

**Word Warden** is a GitHub action that spellchecks markdown or other files in
your repository. It uses `aspell` under the hood, checking your text against a
dictionary for the language of your chose, plus a personal dictionary with your
own approved words.

## Usage

### The simple case

Simply include the action `gevhaz/word-warden` in your job like so:

```yaml
jobs:
  spellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: gevhaz/word-warden@v1.0.0
```

If it finds any words that you consider false positives, add them to the file
`.github/data/project-dictionary.txt` in your repository (or any other
dictionary you specify with the `files` option). Make sure to add:

```text
personal_ws-1.1 en 1000 utf-8
```

as the first line in the file. Replace `en` with the language code of your
language if it's not English.

### Optional input arguments

By default,the action checks all markdown files in your repository (that have
the `.md` extension) but you can also select any other files by specifying the
`files` option. Glob expressions may be used.

The default language is American English (`en_US`). Set any other language that
`aspell` accepts with the `language` argument to the Action.

By default the action looks for your personal dictionary at
`.github/data/project-dictionary.txt` and if you don't have one there, it acts
as if you had an empty one. Specify any other location for you dictionary with
the `dictionary` key.

If you need to preprocess your script with sed – for example to remove parts of
files that shouldn't be spellchecked – you can use the `preprocessing_script`
argument. You can find more details under [Common issues](#common-issues).

Here is an example with all options used:

```yaml
jobs:
  spellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: gevhaz/word-warden@v1.0.0
        with:
          language: en_IN
          dictionary: ./words.txt
          files: README.md
          preprocessing_script: path/to/script.sed
```

## Common issues

**Pandoc crashes**: Pandoc is used to convert the files to HTML in one stage. It
uses the file extension to determine the filetype of your file, so make sure
it's correct.

**Some content needs to be removed before spellchecking**: If the spellchecking
script has trouble processing your file, you might want to try to preprocess it.
You do this with the `preprocessing_script` input variable. Supply a sed script
(basically an ordinary sed command, but in a file). It will be run on all files
that are the target of spellchecking.

If the preprocessing script affects files you don't want preprocessed, you might
have to add two different spellcheck jobs where you target different files in
each.

**Listed misspelled word cannot be found in text**: When converting from
markdown to HTML and back, Pandoc sometimes adds stuff. Try converting the file
in question to HTML manually and look for the word there:
`pandoc <file> | grep <word>`.

## Development

### Contributing

Contributions are welcome. Feel free to open bug reports and feature requests.
Pull requests will be reviewed and possibly merged.

### Releasing

Releases are done from the `main` branch. These are the steps:

1. Add a new pull request with a step-up commit that updates:
    - the changelog,
    - the default `word_warden_ref` in `action.yaml` with the version number you
      are about to release, and
    - the version number in the README, if relevant.
2. Merge it to `main`.
3. Add an annotated release tag with the version number, on the step-up commit
on the `main` branch.
4. Push the tag.
5. Manually create a release in the GitHub web interface (will be automated
later).

### Using unreleased content

Word Warden follows semver. Normally when using it, a version tag (see
[Releases](https://github.com/gevhaz/Word-Warden/releases)) should be used to
specify what reference of it should be used. If you want to use a specific
commit rather than a tag, you need to set the `word_warden_ref` input parameter
to the hash of the same commit you are checking out with `uses`.

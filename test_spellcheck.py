"""Test for the spellcheck script."""
import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

import pytest

import spellcheck
from spellcheck import BLUE, BOLD, MAGENTA, RED, RESET

PASSING_CONTENT: Final = """# Some markdown

A paragraph with a [link](https://examplllle.com), a code block:

```yaml
key: valueeeee
```

and another style of link: <https://examplllle.com>.

All URLs and code have spelling errors, since they will be removed
anyway.
"""
SHORT_PASSING_CONTENT: Final = "This is correctly spelled."
FAILING_CONTENT: Final = PASSING_CONTENT + "\n\nmisspelllledword."


@pytest.fixture
def create_passing_test_file(tmp_path):
    """Create a markdown file for tests that should pass spellcheck."""
    filepath = tmp_path / "passing_test_file.md"
    filepath.write_text(PASSING_CONTENT)
    return filepath


@pytest.fixture
def create_short_passing_test_file(tmp_path):
    """Create a markdown file for tests that should pass spellcheck."""
    filepath = tmp_path / "passing_test_file.md"
    filepath.write_text(SHORT_PASSING_CONTENT)
    return filepath


@pytest.fixture
def create_failing_test_file(tmp_path):
    """Create a markdown file for tests that should pass spellcheck."""
    filepath = tmp_path / "failing_test_file.md"
    filepath.write_text(FAILING_CONTENT)
    return filepath


def test_prune_content_good():
    """Test pruning content from md file.

    Test that different kinds of markdown content is removed as
    expected. In particular, there is inline code, code blocks and URLs
    in the original markdown but it is removed after being pruned.
    """
    with open("test_resources/all_parameters.md") as f:
        input_content = f.read()
    with TemporaryDirectory() as dir:
        test_file = Path(dir) / "test_file.md"
        with open(test_file, "w") as f:
            f.write(input_content)
        actual_pruned = spellcheck.prune_content(test_file)
        expected_pruned = (
            "# AWAKENING"
            "\n"
            "\nSlower, he walked along in his thoughts and asked himself:"
            "\n"
            "\n> But what is this, you have sought to learn from teachings and from"
            "\n> teachers, and what they, who have taught you much, were still unable"
            "\n> to teach you?"
            "\n"
            "\nAnd he found:"
            "\n"
            "\n> It was the self, the purpose and essence of which I sought to learn."
            "\n> It was the self, I wanted to free myself from, which I sought to"
            "\n> overcome. But I was not able to overcome it, could only deceive it,"
            "\n> could only flee from it, only hide from it. Truly, no thing in this"
            "\n> world has kept my thoughts thus busy, as this my very own self, this"
            "\n> mystery of me being alive, of me being one and being separated and"
            "\n> isolated from all others, of me being Siddhartha! And there is no"
            "\n> thing in this world I know less about than about me, about Siddhartha!"
            "\n"
            "\nHaving been pondering while slowly walking along, he now stopped as"
            "\nthese thoughts caught hold of him, and right away another thought sprang"
            "\nforth from these, a new thought, which was:"
            "\n"
            "\n> That I know nothing about myself, that Siddhartha has remained thus"
            "\n> alien and unknown to me, stems from one cause, a single cause: I was"
            "\n> afraid of myself, I was fleeing from myself! I searched Atman, I"
            "\n> searched Brahman, I was willing to dissect my self and peel off all of"
            "\n> its layers, to find the core of all peels in its unknown interior, the"
            "\n> Atman, life, the divine part, the ultimate part. But I have lost"
            "\n> myself in the process."
            "\n"
            "\nSiddhartha opened his eyes and looked around, a smile filled his face"
            "\nand a feeling of awakening from long dreams flowed through him from his"
            "\nhead down to his toes. And it was not long before he walked again,"
            "\nwalked quickly like a man who knows what he has got to do."
            "\n"
            "\nwordindictionary"
            "\n"
        )
        assert actual_pruned == expected_pruned


def test_prune_content_non_existent_file():
    """Test pruning content from non-existent file fails."""
    non_existent_file = Path("test_resources/this_file_does_not_exist")
    with pytest.raises(spellcheck.SpellcheckError) as exc_info:
        spellcheck.prune_content(non_existent_file)
    expected_error = (
        "Can't spellcheck non-existent file: test_resources/this_file_does_not_exist"
    )
    assert str(exc_info.value) == expected_error


def test_prune_content_bad_file_content():
    """Test pruning a file with known bad content fails as expected."""
    with open("test_resources/weird-front-matter-1.markdown") as f:
        input_content = f.read()
    with TemporaryDirectory() as dir:
        test_file = Path(dir) / "test_file.md"
        with open(test_file, "w") as f:
            f.write(input_content)
        with pytest.raises(spellcheck.SpellcheckError) as exc_info:
            spellcheck.prune_content(test_file)
        expected_exception = re.compile(
            r"Failed to convert '.*test_file.md' "
            r"to HTML running: pandoc .*/test_file.md --to html"
        )
        assert re.match(expected_exception, str(exc_info.value))


def test_word_context_good(create_short_passing_test_file):
    """Test that provided words are highlighted."""
    words = ["correctly"]
    filepath = create_short_passing_test_file
    with open(filepath, "r") as f:
        actual_highlight = spellcheck.words_context(
            f.readlines(),
            words=words,
        )
    expected_highlight = f"{BLUE}1:{RESET} This is {RED}correctly{RESET} spelled."
    assert actual_highlight == expected_highlight


def test_word_context_no_highlight_substring(create_short_passing_test_file):
    """Test that only exact word matches are highligted.

    An initial version of the spellcheck script simply highlighted all
    series of characters matching a word from the list of words to
    highlight. It should only highlight cases where that exact word is.
    Different cases are set up to test what will count as a word.
    """
    words = ["is"]
    filepath = create_short_passing_test_file
    with open(filepath, "r") as f:
        actual_highlight = spellcheck.words_context(
            content_lines=f.readlines(),
            words=words,
        )
    expected_highlight = f"{BLUE}1:{RESET} This {RED}is{RESET} correctly spelled."
    assert actual_highlight == expected_highlight


def test_word_context_no_input(create_short_passing_test_file):
    """Test that input with no text or words is handled well.

    Basically, if there are no words, we test that the text is returned
    as it was before. If there is no text, it should also be returned as
    it was, and in neither case should it crash.
    """
    words = ["is"]
    no_words = []
    no_text = [""]

    filepath = create_short_passing_test_file
    with open(filepath, "r") as f:
        actual_highlight_1 = spellcheck.words_context(
            content_lines=f.readlines(),
            words=no_words,
        )
        assert actual_highlight_1 == SHORT_PASSING_CONTENT

        actual_highlight_2 = spellcheck.words_context(
            content_lines=no_text,
            words=words,
        )
        assert actual_highlight_2 == ""

    actual_highlight_3 = spellcheck.words_context(
        content_lines=no_text,
        words=no_words,
    )
    assert actual_highlight_3 == ""


def test_word_context_word_not_found(create_short_passing_test_file):
    """Test text is just returned if a provided word is missing."""
    words = ["notfound"]

    filepath = create_short_passing_test_file
    with open(filepath, "r") as f:
        content_lines = f.readlines()
    actual_highlight_1 = spellcheck.words_context(
        content_lines=content_lines,
        words=words,
    )
    assert actual_highlight_1 == "".join(content_lines)


def test_wrap_print_wraps_okay(capsys):
    """Test that text is wrapped as it should, not breaking in words."""
    input_text = (
        "This myth, this rumour, this legend resounded, its fragrance rose up, "
        "here and there; in the towns, the Brahmans spoke of it and in the "
        "forest, the Samanas; again and again, the name of Gotama, the Buddha "
        "reached the ears of the young men, with good and with bad talk, with "
        "praise and with defamation."
    )

    spellcheck.wrap_print(input_text, width=72)
    actual_text = capsys.readouterr().out
    print(actual_text)

    expected_text = (
        "This myth, this rumour, this legend resounded, its fragrance rose up,"
        "\nhere and there; in the towns, the Brahmans spoke of it and in the"
        "\nforest, the Samanas; again and again, the name of Gotama, the Buddha"
        "\nreached the ears of the young men, with good and with bad talk, with"
        "\npraise and with defamation."
        "\n\n"
    )

    assert actual_text == expected_text


def test_main_output_okay(capsys):
    """Try spellchecking the integration test sample files.

    Try spellchecking the integration test sample files and check that
    the output of the script is as expected in its totality. It's a
    pretty long output so it is stored in resource files.
    """
    expected_output = []
    with open("test_resources/script_output_dump.txt", "r") as f:
        for line in f:
            expected_output.append(
                line.rstrip("\n").format(
                    RESET=RESET,
                    BOLD=BOLD,
                    RED=RED,
                    MAGENTA=MAGENTA,
                    BLUE=BLUE,
                )
            )

    args = argparse.Namespace(
        dictionary_path=".github/data/yaml-wordlist.txt",
        files=[
            "test_resources/all_parameters.md",
            "test_resources/file with spaces.md",
            "test_resources/sample.yaml",
        ],
        document_language="en_US",
    )
    spellcheck.main(args)
    actual_output = capsys.readouterr().out.splitlines()
    assert expected_output == actual_output

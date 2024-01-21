"""Scrip for spellchecking files using aspell.

Spellcheck the provided files with aspell using the provided aspell
personal dictionary. That is, the first must be something like
'personal_ws-1.1 <language> 1000 utf-8'. The language should be
specified with a locale code like 'en_IN' Example usage:

    $ python3 --dictionary wordlist.txt --language en_IN README.md

Requirements:

    - aspell
    - pandoc
"""
import argparse
import re
import subprocess
import sys
import textwrap
from argparse import Namespace
from pathlib import Path
from subprocess import CalledProcessError

from bs4 import BeautifulSoup

# ANSI escape codes
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BLACK = "\033[30m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
REVERSED = "\033[7m"
RESET = "\033[0m"

TEXTWIDTH = 80


class SpellcheckError(Exception):
    """Default custom exception for the Spellcheck script."""

    pass


class CheckedFile:
    """Class for representing a file under spelling evaluation."""

    def __init__(self, filepath: str, misspelled_words: list[str]) -> None:
        """Initialize a CheckedFile object."""
        self.filepath = filepath
        self.misspelled_words = misspelled_words

    def __str__(self) -> str:
        """Print a string representation of the CheckedFile object."""
        return self.filepath


def main(args: Namespace) -> int:
    """Do all the functionality of the script.

    This is the main function. It holds the primary logic and the
    structure of the script.

    Args:
        args: Command line arguments provided to the script.

    Returns:
        The exit code that the script should  exit with.
    """
    wrap_print(f"{BOLD}RUNNING SPELLCHECK{RESET}")
    good_files: list[CheckedFile] = []
    bad_files: list[CheckedFile] = []

    for filepath in args.files:
        pruned_content = prune_content(Path(filepath))

        spellcheck_cmd = [
            "aspell",
            "--home-dir",
            ".",
            "--mode",
            "markdown",
            "--lang",
            args.document_language,
        ]

        if args.dictionary_path:
            if not isinstance(args.dictionary_path, str):
                raise SpellcheckError("Dictionary path must be a single string")
            if not Path(args.dictionary_path).exists():
                raise SpellcheckError(
                    "No file exists at the specified dictionary path."
                )
            spellcheck_cmd += [
                "--personal",
                args.dictionary_path,
            ]

        spellcheck_cmd.append("list")
        try:
            result = subprocess.run(
                spellcheck_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                input=pruned_content,
                check=True,
            )
        except CalledProcessError as e:
            raise SpellcheckError(
                f"Failed to spellcheck {filepath}: "
                f"Running '{e.cmd}' failed with output: {e.stderr}"
            )
        standard_out = result.stdout.strip()
        # standard_error = result.stderr
        # exit_code = result.returncode

        if standard_out:
            misspelled_words = [w.strip() for w in standard_out.split("\n")]
            bad_files.append(
                CheckedFile(
                    filepath=filepath,
                    misspelled_words=misspelled_words,
                )
            )
        else:
            good_files.append(CheckedFile(filepath=filepath, misspelled_words=[]))

    if good_files:
        wrap_print("The following file(s) are free from spelling errors:\n")

        for good_file in good_files:
            print(f"  - {good_file.filepath}")

        print()
        if not bad_files:
            print(f"{GREEN}All checked files are free from misspellings!{RESET}")

    if bad_files:
        wrap_print(
            f"Found {BOLD}{len(bad_files)}{RESET} files with potentially misspelled "
            "words."
        )
        for bad_file in bad_files:
            wrap_print(
                f"The file {MAGENTA}{BOLD}{bad_file.filepath}{RESET} has potentially "
                "misspelled words, highlighted in their context here:"
            )
            with open(bad_file.filepath, "r") as f:
                print(words_context(f.readlines(), bad_file.misspelled_words))
            wrap_print(
                "All occurrences of the detected potentially misspelled words are "
                "highlighted, but inline code, code blocks, and the URL part of "
                "markdown links do not actually trigger the spellcheck and do not "
                "need to be changed. The potentially misspelled words are:"
            )
            for bad_word in set(bad_file.misspelled_words):
                print(f"  - {RED}{bad_word}{RESET}")
            print()
        wrap_print(
            "If you think any word marked as misspelled is actually correct in your "
            "chosen language, please update your local dictionary at:"
        )
        wrap_print(f"{args.dictionary_path}")
        wrap_print(
            "If the word in question is more 'inline code' than natural language, you "
            "can circumvent spellchecking by using backticks (`) since inline code is "
            "not spellchecked."
        )
        wrap_print("The following file(s) may have spelling errors:")
        for bad_file in bad_files:
            print(f"  - {bad_file.filepath}")
        print(f"\n{RED}Some checked files may have spelling errors!{RESET}")
        return 1

    return 0


def wrap_print(text: str, width: int = TEXTWIDTH, end: str = "\n\n") -> None:
    """Print text wrapped at given width and empty line at end.

    Args:
        text: The text to print.
        width: The line length to wrap the text at.
        end: The string to print at the end  of the text.
    """
    print(textwrap.fill(text, width=width), end=end)


def words_context(content_lines: list[str], words: list[str]) -> str:
    """Highlight words in their context in the provided lines of text.

    Args:
        content_lines: The lines of text in which to show word context.
        words: The list of words to show in their context.

    Returns:
        All lines containing any of the specified words, and the
        surrounding lines above and below, with highlighting added to
        the words in red and line numbers added to the start of the
        line.
    """
    if len(words) == 0 or len(content_lines) == 0:
        return "".join(content_lines)
    # Find line numbers with misspelled words, and highlight those words
    # in the text in red color.
    match_lines: set[int] = set()
    for index, line in enumerate(content_lines):
        for word in words:
            if re.search(rf"\b{word}\b", line):
                match_lines.add(index)
                line = re.sub(rf"\b{word}\b", f"{RED}{word}{RESET}", line)
        content_lines[index] = line

    print_lines: set[int] = set()
    for match_line in match_lines:
        if match_line > 0:
            print_lines.add(match_line - 1)
        if match_line < len(content_lines) - 1:
            print_lines.add(match_line + 1)
        print_lines.add(match_line)

    if not print_lines:
        return "".join(content_lines)

    all_context: list[str] = []
    last_print_line = sorted(print_lines)[0]
    line_number_width = len(str(len(content_lines) + 1))
    for print_line in sorted(print_lines):
        if print_line - last_print_line > 1:
            all_context.append(f"{BLUE}{'-' * line_number_width}{RESET}\n")
        line_number = f"{print_line + 1:{line_number_width}}:"
        all_context.append(f"{BLUE}{line_number}{RESET} {content_lines[print_line]}")
        last_print_line = print_line
    return "".join(all_context)


def prune_content(filepath: Path) -> str:
    """Remove code and flatten links for filepath.

    Args:
        filepath: Path to file which to prune.

    Return:
        String with text in markdown format, with inline code, code
        blocks, and links removed if Pandoc can discover the file
        format automatically, otherwise the raw content of the file.

    Raises:
        SpellcheckError: If file doesn't exist or a conversion from or
                         to HTML fails.
    """
    if not Path(filepath).exists():
        raise SpellcheckError(f"Can't spellcheck non-existent file: {filepath}")

    try:
        pandoc_to_html_result = subprocess.run(
            ("pandoc", str(filepath), "--to", "html"),
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
    except CalledProcessError as e:
        raise SpellcheckError(
            f"Failed to convert '{filepath}' to HTML: "
            f"Running '{e.cmd}' failed with output: {e.stderr}"
        )

    html_version = pandoc_to_html_result.stdout.strip()
    soup = BeautifulSoup(html_version, "html.parser")

    for code_tag in soup.find_all("code"):
        code_tag.decompose()

    for pre_tag in soup.find_all("div", class_="sourceCode"):
        pre_tag.decompose()

    for a_tag in soup.find_all("a"):
        a_tag.replace_with(a_tag.get_text())

    pruned_html = str(soup)
    pruned_html = re.sub(r"https://[\S]*", "", pruned_html)
    try:
        pandoc_to_markdown_result = subprocess.run(
            ("pandoc", "--from", "html", "--to", "markdown"),
            stdout=subprocess.PIPE,
            text=True,
            check=True,
            input=pruned_html,
        )
    except CalledProcessError as e:
        raise SpellcheckError(
            f"Failed to convert '{filepath}' back to markdown from HTML: "
            f"Running '{e.cmd}' failed with output: {e.stderr}"
        )
    pruned_markdown = pandoc_to_markdown_result.stdout

    return pruned_markdown


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "\nSpellcheck the provided files with aspell using the provided aspell"
            "personal dictionary. That is, the first must be something like"
            "'personal_ws-1.1 <language> 1000 utf-8'. The language should be"
            "specified with a locale code like 'en_IN' Example usage:"
            "\n"
            "\n    $ python3 --dictionary wordlist.txt --language en_IN README.md"
            "\n"
            "\nRequirements:"
            "\n"
            "\n    - aspell"
            "\n    - pandoc"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="List of files to spellcheck",
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        default="en_US",
        dest="document_language",
        help=(
            "The locale code of the language in which the provided files are written "
            "(default: en_US)."
        ),
    )
    parser.add_argument(
        "-d",
        "--dictionary",
        dest="dictionary_path",
        required=True,
        type=str,
        help=(
            "Path to aspell personal dictionary with words to accept "
            "(must have 'personal_ws-1.1 <language> 1000 utf-8') on the first line."
        ),
    )
    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except SpellcheckError as e:
        print(f"The Spellcheck script encountered a fatal error: {e}", file=sys.stderr)
        sys.exit(1)

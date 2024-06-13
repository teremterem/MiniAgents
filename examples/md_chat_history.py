"""
Parse a chat history in markdown format (work in progress).
TODO Oleksandr: this is a temporary example that will be deleted when the "history-in-md" utility is implemented.
"""

from pprint import pprint

from markdown_it import MarkdownIt


def main() -> None:
    """
    Main function.
    """
    md = MarkdownIt()
    text = """\
user
---------------
hello hello
how are
- you
doing

assistant
---------------
fine
"""
    tokens = md.parse(text)
    pprint(tokens)


if __name__ == "__main__":
    main()

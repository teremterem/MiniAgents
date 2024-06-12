"""
Parse a chat history in markdown format (work in progress).
"""

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
    print(tokens)


if __name__ == "__main__":
    main()

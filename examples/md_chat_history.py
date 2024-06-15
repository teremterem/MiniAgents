"""
Parse a chat history in markdown format (work in progress).
TODO Oleksandr: this is a temporary example that will be deleted when the "history-in-md" utility is implemented.
"""

from pathlib import Path

from markdown_it import MarkdownIt

CHAT_MD_FILE = Path(__file__).parent / "../../talk-about-miniagents/CHAT.md"


def main() -> None:
    """
    Main function.
    """
    md = MarkdownIt()
    tokens = md.parse(CHAT_MD_FILE.read_text(encoding="utf-8"))
    print()
    print()
    print()
    # pprint(tokens)
    for token in tokens:
        print(token.map, token.type, token.tag, token.level, "-----", token.content[:50], "-----")
    print()
    print()
    print()


if __name__ == "__main__":
    main()

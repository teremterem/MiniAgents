"""
Parse a chat history in markdown format (work in progress).
TODO Oleksandr: this is a temporary example that will be deleted when the "history-in-md" utility is implemented.
"""

from pathlib import Path
from pprint import pprint

from markdown_it import MarkdownIt

# CHAT_MD_FILE = Path(__file__).parent / "../../../talk-about-miniagents/CHAT.md"
CHAT_MD_FILE = Path(__file__).parent / "sample.md"


def main() -> None:
    """
    Main function.
    """
    md = MarkdownIt()
    md_content = CHAT_MD_FILE.read_text(encoding="utf-8")
    md_tokens = md.parse(md_content)
    print()
    print()
    print()
    for md_token in md_tokens:
        if md_token.type == "heading_open":
            print()
            print()
            print()
        children = md_token.children
        md_token.children = None
        pprint(md_token)
        if md_token.type not in ("heading_open", "heading_close") and children:
            for child in children:
                print(" ", child)
        if md_token.type == "heading_close":
            print()
            print()
            print()
        print()
        # print(token.map, token.type, token.tag, token.level, "-----", token.content[:50], "-----")
    print()
    print()
    print()


if __name__ == "__main__":
    main()

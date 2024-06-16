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
    md_content = CHAT_MD_FILE.read_text(encoding="utf-8")
    md_lines = md_content.split("\n")
    tokens = md.parse(md_content)
    print()
    print()
    print()
    # pprint(tokens)
    token_iterator = iter(tokens)
    for token in token_iterator:
        if token.type == "heading_open":
            token_after_heading_open = next(token_iterator)  # an unorthodox trick
            token_before_heading_close = token_after_heading_open

            for token_ in token_iterator:
                # ATTENTION! here we are iterating over the same iterator (an unorthodox trick)
                if token_.type == "heading_close":
                    break
                token_before_heading_close = token_

            # print(token.map, token.type, token.tag, token.level, "-----", token.content[:50], "-----")
            print()
            print()
            print("\n".join(md_lines[token_after_heading_open.map[0] : token_before_heading_close.map[1]]))
            print()
            print()
        # elif token.type == "heading_close":
        #     print(token.map, token.type, token.tag, token.level, "-----", token.content[:50], "-----")
    print()
    print()
    print()


if __name__ == "__main__":
    main()

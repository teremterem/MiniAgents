"""
This file contains prompts for `self_dev`.
"""

SYSTEM_HERE_ARE_REPO_FILES = (  # TODO Oleksandr: improve this instruction ?
    "Here are the source files of a Python framework that I'm building that goes by the name of MiniAgents."
)
SYSTEM_IMPROVE_README = (
    "Please improve/finalize the README.md in this framework:\n"
    "\n"
    "1) Take care of TODOs\n"
    "2) Improve descriptions of things, where necessary\n"
    "3) Get rid of repetitions\n"
    "4) Fix code examples if broken (if you see inconsistencies with the provided source code of the framework)\n"
    "5) Do everything the user asks for\n"
    "\n"
    "Make sure to pay a lot of attention to the framework's source code while doing all of the above, "
    "because the current version(s) of README.md might not be up to date or might contain errors."
)

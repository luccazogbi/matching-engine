"""Entry point for `python -m matching_engine`.

Kept separate from __init__.py, which runs on every import of the package: a test importing
matching_engine.order should not drag the command line interface in with it.
"""

from .cli import main

main()

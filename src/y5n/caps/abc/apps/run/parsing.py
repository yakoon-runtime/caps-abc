"""ABC run input syntax: split a submitted line into keyed entries.

The key is a retrieval cue, not a filter: an entry belongs to the key
character it begins with (A-Z or 0-9), and an explicit ``<key>:`` prefix
overrides that assignment. The prefix is input syntax and never becomes
part of the stored text. Entries are never interpreted beyond that.
"""

from __future__ import annotations

import re

KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

_OVERRIDE = re.compile(r"^\s*([A-Za-z0-9]):\s*(.*)$", re.DOTALL)


def parse_entries(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Parse one submitted input line into ``(key, entry)`` pairs.

    Semicolon is the batch separator; comma is ordinary content. Parts
    are trimmed. A part is stored only when the explicit override matches
    or its FIRST character is an ASCII A-Z letter or a digit — later
    characters are never scanned. Letters normalize to uppercase, digits
    stay as they are. Returns the pairs and the rejected parts (with
    their original text, for feedback).
    """
    result: list[tuple[str, str]] = []
    rejected: list[str] = []
    for raw in text.split(";"):
        part = raw.strip()
        if not part:
            continue
        override = _OVERRIDE.match(part)
        if override:
            key = override.group(1).upper()
            entry = override.group(2).strip()
            if entry:
                result.append((key, entry))
            else:
                rejected.append(part)
            continue
        first = part[0]
        if first.isascii() and (first.isalpha() or first.isdigit()):
            result.append((first.upper(), part))
        else:
            rejected.append(part)
    return result, rejected

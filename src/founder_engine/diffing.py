"""Before/after comparison of drafts. Floris's edits are the training signal for his voice file."""

from __future__ import annotations

import difflib


def word_diff(before: str, after: str) -> str:
    """Readable word-level diff: [-removed-] {+added+}."""
    a, b = before.split(), after.split()
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(" ".join(a[i1:i2]))
        if op in ("delete", "replace"):
            out.append("[-" + " ".join(a[i1:i2]) + "-]")
        if op in ("insert", "replace"):
            out.append("{+" + " ".join(b[j1:j2]) + "+}")
    return " ".join(x for x in out if x)


def change_ratio(before: str, after: str) -> float:
    """0.0 = identical, 1.0 = completely rewritten. Used to track Floris's lift over time."""
    if not before and not after:
        return 0.0
    return round(1 - difflib.SequenceMatcher(a=before.split(), b=after.split(), autojunk=False).ratio(), 3)

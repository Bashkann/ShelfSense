"""Conservative placement-slot parsing."""

from dataclasses import dataclass

LETTER_CODES = ("A", "B", "C", "D")
WORD_CODES = ("ust", "orta", "alt", "kasa")


class SlotSyntaxError(ValueError):
    """A slot uses unsupported or ambiguous syntax."""

    def __init__(self, raw: str, normalized: str, reason: str):
        self.raw = raw
        self.normalized = normalized
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ParsedSlot:
    """Normalized source spelling plus expanded atomic codes."""

    raw: str
    normalized: str
    codes: tuple[str, ...]


def parse_slot(raw: str) -> ParsedSlot:
    """Parse only the frozen letter/list/range and word syntax."""

    stripped = raw.strip()
    if not stripped:
        raise SlotSyntaxError(raw, stripped, "slot is empty")

    if "," in stripped:
        if "-" in stripped:
            raise SlotSyntaxError(raw, stripped, "lists cannot contain ranges")
        tokens = [part.strip().upper() for part in stripped.split(",")]
        normalized = ",".join(tokens)
        if any(token not in LETTER_CODES for token in tokens):
            raise SlotSyntaxError(raw, normalized, "lists support only A/B/C/D")
        if len(tokens) != len(set(tokens)):
            raise SlotSyntaxError(raw, normalized, "duplicate atomic level code")
        return ParsedSlot(raw, normalized, tuple(tokens))

    if "-" in stripped:
        parts = [part.strip().upper() for part in stripped.split("-")]
        normalized = "-".join(parts)
        if len(parts) != 2 or any(part not in LETTER_CODES for part in parts):
            raise SlotSyntaxError(raw, normalized, "ranges support only A/B/C/D")
        start = LETTER_CODES.index(parts[0])
        end = LETTER_CODES.index(parts[1])
        if start >= end:
            raise SlotSyntaxError(raw, normalized, "range must be strictly ascending")
        return ParsedSlot(raw, normalized, LETTER_CODES[start : end + 1])

    if len(stripped) == 1:
        normalized = stripped.upper()
        if normalized in LETTER_CODES:
            return ParsedSlot(raw, normalized, (normalized,))

    normalized = stripped.lower()
    if normalized in WORD_CODES:
        return ParsedSlot(raw, normalized, (normalized,))
    raise SlotSyntaxError(raw, normalized, "unknown atomic level code")

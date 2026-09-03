"""Explicit and fallback shelf-level resolution."""

from dataclasses import dataclass

from shelfsense.db.importer.source import ExplicitLevelSource


@dataclass(frozen=True)
class LevelDefinition:
    code: str
    level_order: int
    description: str


ABCD = (
    LevelDefinition("A", 1, "en üst raf"),
    LevelDefinition("B", 2, "üst-orta raf"),
    LevelDefinition("C", 3, "alt-orta raf"),
    LevelDefinition("D", 4, "en alt raf"),
)
BEVERAGE = (
    LevelDefinition("ust", 1, "üst raf"),
    LevelDefinition("orta", 2, "orta raf"),
    LevelDefinition("alt", 3, "alt raf"),
)
PRODUCE = (LevelDefinition("kasa", 1, "kasa"),)
TEMPLATES = (ABCD, BEVERAGE, PRODUCE)


class LevelResolutionError(ValueError):
    """A shelf level structure cannot be represented by frozen templates."""

    def __init__(self, category: str, reason: str, **details: object):
        self.category = category
        self.reason = reason
        self.details = {"reason": reason, **details}
        super().__init__(reason)


def detect_template(observed_codes: set[str]) -> tuple[LevelDefinition, ...]:
    """Select the one full template containing the observed atomic codes."""

    matches = [template for template in TEMPLATES if observed_codes <= _codes(template)]
    if len(matches) != 1:
        raise LevelResolutionError(
            "LEVEL_TEMPLATE_DETECTION_FAILED",
            "observed vocabulary is mixed, unknown, or ambiguous",
            parsed_codes=sorted(observed_codes),
        )
    return matches[0]


def validate_explicit_levels(
    levels: list[ExplicitLevelSource],
) -> tuple[LevelDefinition, ...]:
    """Validate an explicit structure against one complete known template."""

    if not levels:
        raise _unsupported("explicit levels cannot be empty")

    normalized: list[tuple[str, int]] = []
    for level in levels:
        code = _normalize_code(level.code)
        if not code:
            raise _unsupported("explicit level code cannot be empty")
        if level.order <= 0:
            raise _unsupported("explicit level order must be positive")
        normalized.append((code, level.order))

    codes = [code for code, _ in normalized]
    orders = [order for _, order in normalized]
    if len(codes) != len(set(codes)):
        raise _unsupported("explicit level codes must be unique")
    if len(orders) != len(set(orders)):
        raise _unsupported("explicit level orders must be unique")

    for template in TEMPLATES:
        expected = [(level.code, level.level_order) for level in template]
        if sorted(normalized) == sorted(expected):
            return template
    raise _unsupported("explicit vocabulary/order does not match a supported template")


def _normalize_code(code: str) -> str:
    stripped = code.strip()
    return stripped.upper() if len(stripped) == 1 else stripped.lower()


def _codes(template: tuple[LevelDefinition, ...]) -> set[str]:
    return {level.code for level in template}


def _unsupported(reason: str) -> LevelResolutionError:
    return LevelResolutionError("UNSUPPORTED_EXPLICIT_LEVEL_STRUCTURE", reason)

"""Frozen slot parser and level-template tests."""

import pytest

from shelfsense.db.importer.levels import LevelResolutionError, detect_template
from shelfsense.db.importer.slots import SlotSyntaxError, parse_slot


@pytest.mark.parametrize(
    ("raw", "normalized", "codes"),
    [
        ("A", "A", ("A",)),
        ("A-D", "A-D", ("A", "B", "C", "D")),
        ("A-C", "A-C", ("A", "B", "C")),
        ("B-D", "B-D", ("B", "C", "D")),
        ("B,D", "B,D", ("B", "D")),
        ("A,C", "A,C", ("A", "C")),
        (" a-d ", "A-D", ("A", "B", "C", "D")),
        (" B , d ", "B,D", ("B", "D")),
        (" UST ", "ust", ("ust",)),
        ("orta", "orta", ("orta",)),
        ("alt", "alt", ("alt",)),
        ("Kasa", "kasa", ("kasa",)),
    ],
)
def test_supported_slot_syntax(raw, normalized, codes) -> None:
    parsed = parse_slot(raw)
    assert parsed.normalized == normalized
    assert parsed.codes == codes


@pytest.mark.parametrize(
    "raw",
    ["D-A", "C-A", "D-B", "ust-alt", "A/ B", "A,ust", "A,A", "", "1"],
)
def test_invalid_slot_syntax_is_rejected(raw) -> None:
    with pytest.raises(SlotSyntaxError):
        parse_slot(raw)


def test_abcd_subset_selects_full_template() -> None:
    template = detect_template({"A", "D"})
    assert [level.code for level in template] == ["A", "B", "C", "D"]


@pytest.mark.parametrize("codes", [{"A", "ust"}, {"unknown"}])
def test_mixed_or_unknown_template_vocabulary_is_rejected(codes) -> None:
    with pytest.raises(LevelResolutionError) as caught:
        detect_template(codes)
    assert caught.value.category == "LEVEL_TEMPLATE_DETECTION_FAILED"

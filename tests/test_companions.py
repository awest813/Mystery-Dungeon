"""Tests for Phase 10 – romanceable companions."""
import pytest

from entities.companion import (
    CompanionDef, load_companion_def,
    SUPPORT_RANKS, SUPPORT_THRESHOLDS,
)


def test_load_companion_def():
    lyra = load_companion_def("lyra")
    assert lyra is not None
    assert lyra.id == "lyra"
    assert lyra.role == "Mage"
    assert "mushroom" in lyra.preferred_items


def test_load_all_companions():
    for cid in ["lyra", "brom", "mira", "sable", "finn"]:
        d = load_companion_def(cid)
        assert d is not None, f"Missing companion def for {cid}"
        assert d.name
        assert d.max_hp > 0
        assert d.attack_power > 0
        assert d.preferred_items
        assert d.disliked_items


def test_support_thresholds():
    assert SUPPORT_THRESHOLDS["C"] == 0
    assert SUPPORT_THRESHOLDS["B"] == 25
    assert SUPPORT_THRESHOLDS["A"] == 55
    assert SUPPORT_THRESHOLDS["S"] == 85
    assert len(SUPPORT_RANKS) == 4


def test_companion_def_fields():
    d = load_companion_def("brom")
    assert d.role == "Knight"
    assert d.max_hp == 35
    assert "iron_ore" in d.preferred_items
    assert "slime_gel" in d.disliked_items

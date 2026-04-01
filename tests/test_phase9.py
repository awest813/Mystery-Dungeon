"""Tests for Phase 9 – cooking, crafting, garden, calendar."""
import json
import os
import tempfile

import pytest

from game.calendar import Calendar, SEASONS, DAYS_PER_SEASON
from world.kitchen import load_recipes, can_cook, cook, CookingRecipe, MealBuff
from world.workbench import load_blueprints, can_craft, craft
from world.garden import (
    load_crop_definitions, get_crop_defs, get_garden_capacity,
    create_plot, harvest_plot, water_plot, CropPlot,
)


# -- Calendar --

def test_calendar_day_1_is_spring():
    cal = Calendar(1)
    assert cal.season == "Spring"
    assert cal.day_in_season == 1

def test_calendar_season_progression():
    cal = Calendar(DAYS_PER_SEASON + 1)
    assert cal.season == "Summer"

def test_calendar_autumn():
    cal = Calendar(DAYS_PER_SEASON * 2 + 1)
    assert cal.season == "Autumn"

def test_calendar_winter():
    cal = Calendar(DAYS_PER_SEASON * 3 + 1)
    assert cal.season == "Winter"

def test_calendar_advance_day():
    cal = Calendar(1)
    cal.advance_day()
    assert cal.day == 2

def test_calendar_week_in_season():
    cal = Calendar(8)
    assert cal.week_in_season == 2

def test_calendar_to_dict_roundtrip():
    cal = Calendar(15)
    d = cal.to_dict()
    cal2 = Calendar.from_dict(d)
    assert cal2.day == 15
    assert cal2.season == cal.season


# -- Kitchen --

def test_load_recipes():
    recipes = load_recipes()
    assert len(recipes) == 6

def test_cooking_recipe_has_buff():
    recipes = load_recipes()
    stew = [r for r in recipes if r.id == "hearty_stew"][0]
    assert stew.buff.stat == "max_hp_pct"
    assert stew.buff.value == 20

def test_can_cook_true():
    class P:
        materials = {"mushroom": 5, "meat_chunk": 3}
    recipes = load_recipes()
    stew = [r for r in recipes if r.id == "hearty_stew"][0]
    assert can_cook(stew, P())

def test_can_cook_false():
    class P:
        materials = {"mushroom": 1}
    recipes = load_recipes()
    stew = [r for r in recipes if r.id == "hearty_stew"][0]
    assert not can_cook(stew, P())

def test_cook_spends_ingredients():
    recipes = load_recipes()
    stew = [r for r in recipes if r.id == "hearty_stew"][0]
    class P:
        def __init__(self):
            self.materials = {"mushroom": 5, "meat_chunk": 3}
    p = P()
    assert cook(stew, p)
    assert p.materials["mushroom"] == 3
    assert p.materials["meat_chunk"] == 2
    # Second cook should also work
    p2 = P()
    cook(stew, p2)
    cook(stew, p2)
    assert p2.materials["mushroom"] == 1
    assert p2.materials["meat_chunk"] == 1


# -- Crafting --

def test_load_blueprints():
    bps = load_blueprints()
    assert len(bps) == 7

def test_can_craft_true():
    class P:
        materials = {"herb_bundle": 5, "slime_gel": 3}
        inventory = []
        max_inventory = 10
    bps = load_blueprints()
    antidote = [b for b in bps if b.id == "antidote_potion"][0]
    assert can_craft(antidote, P())

def test_can_craft_false_inventory_full():
    class P:
        materials = {"herb_bundle": 5, "slime_gel": 3}
        inventory = [1] * 10
        max_inventory = 10
    bps = load_blueprints()
    antidote = [b for b in bps if b.id == "antidote_potion"][0]
    assert not can_craft(antidote, P())


# -- Garden --

def test_load_crop_definitions():
    data = load_crop_definitions()
    assert len(data["crops"]) == 5

def test_get_crop_defs():
    defs = get_crop_defs()
    assert "grain" in defs
    assert defs["grain"]["growth_days"] == 2

def test_get_garden_capacity():
    assert get_garden_capacity() == 4

def test_create_plot():
    defs = get_crop_defs()
    plot = create_plot("grain", defs)
    assert plot is not None
    assert plot.crop_id == "grain"
    assert plot.growth_days_needed == 2
    assert not plot.is_ready

def test_plot_advance_day():
    defs = get_crop_defs()
    plot = create_plot("grain", defs)
    assert not plot.is_ready
    plot.advance_day()
    plot.advance_day()
    assert plot.is_ready

def test_plot_advance_day_watered():
    defs = get_crop_defs()
    plot = create_plot("oran_berry", defs)
    assert plot.growth_days_needed == 3
    water_plot(plot)
    plot.advance_day()
    assert plot.growth_days_current == 2
    plot.advance_day()
    assert plot.is_ready

def test_harvest_plot():
    class P:
        inventory = []
        max_inventory = 10
        def pick_up_item(self, item):
            self.inventory.append(item)
            return len(self.inventory) <= self.max_inventory
    defs = get_crop_defs()
    plot = create_plot("grain", defs)
    plot.advance_day()
    plot.advance_day()
    assert plot.is_ready
    assert harvest_plot(plot, P())
    assert plot.growth_days_current == 0

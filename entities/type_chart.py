"""
Elemental type effectiveness chart.
Maps (skill_element, enemy_element_type) -> damage multiplier.

Skill elements: fire, ice, lightning, dark (None = neutral)
Enemy element types: fire, ice, flying, ghost, dark (None = neutral)
"""

TYPE_CHART = {
    # Fire attacks
    ("fire",      "ice"):     2.0,   # fire melts ice
    ("fire",      "fire"):    0.5,   # fire resists fire

    # Ice attacks
    ("ice",       "fire"):    2.0,   # ice quenches fire
    ("ice",       "ice"):     0.5,   # ice resists ice

    # Lightning attacks
    ("lightning", "flying"):  2.0,   # lightning zaps fliers
    ("lightning", "ghost"):   0.5,   # lightning barely hurts ghosts

    # Dark attacks
    ("dark",      "ghost"):   2.0,   # dark banishes ghosts
    ("dark",      "dark"):    0.5,   # dark resists dark
}

# Text labels for log messages
EFFECTIVENESS_LABELS = {
    2.0: "It's super effective!",
    0.5: "It's not very effective...",
}


def get_type_multiplier(skill_element, enemy_element_type):
    """
    Returns the damage multiplier for a skill element vs an enemy's element type.
    Defaults to 1.0 (neutral).
    """
    if skill_element is None or enemy_element_type is None:
        return 1.0
    return TYPE_CHART.get((skill_element, enemy_element_type), 1.0)

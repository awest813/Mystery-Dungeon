# Mystery Dungeon

A PMD-inspired turn-based roguelike built with [Panda3D](https://github.com/panda3d/panda3d).
Explore procedurally generated dungeons, collect loot with randomised affixes, level up your
character, manage a hunger/PP economy, and return to a growing town between runs.

## Current Status

**Phase 7 – Procedural Loot & Enchantment** is complete. **Phase 8 – Town building**
(material nodes, Town Plot construction, forge tiers) is in progress.
See [PLAN.md](PLAN.md) for the full roadmap.

### Implemented Features

| Phase | Feature area |
|-------|-------------|
| 1 | Core Panda3D project, tilemap rendering, player movement, enemy AI placeholder |
| 2 | Procedural room-and-corridor generation, themed floors (Cave / Ice / Fire), item tiles, stairs |
| 3 | Hunger system, gold drops, XP accumulation, JSON save/load |
| 4 | Turn-based combat, enemy AI (chase/attack), floor-scaling enemy stats, spawn system |
| 5 | Smooth camera, hop animation, message log, HUD colour coding, respawn flow |
| 6 | Items (food/potions/weapons/orbs/keys), level-up system, PMD-style 4-slot skill/PP system, status effects, 8 enemy types + dark\_knight boss, traps/water/lava, boss floors every 5 floors |
| 7 | Rarity tiers (Common → Legendary / Cursed), 13-affix system, legendary uniques, item identification, LootGenerator, material drops, Town Forge enchanting/upgrading, item inspection overlay |
| 8 (WIP) | Dungeon material nodes; Town Plot + `data/buildings.json` construction; `completed_buildings` in save; HUD materials line; Forge Lv2 lowers forge costs |

### Key Mechanics

- **Procedural dungeons** — room-and-corridor layouts, up to 12 rooms, three visual themes
- **Turn-based combat** — player acts, then every living enemy takes a turn
- **Skills & PP** — 4 skill slots (Slash, Headbutt, Ember, Ice Shard, Thunder, Shadow Claw, Giga Impact, Heal, Sleep Powder, Toxic); PP restored on returning to town
- **Status effects** — poisoned, burned, confused, paralyzed, asleep
- **Loot system** — weighted per-floor tables; weapons carry rarity tiers and Diablo-style affixes; mystery names revealed by use or Identify Scroll
- **Town Forge** — spend materials farmed from enemies to enchant or upgrade your equipped weapon
- **Save/load** — inventory, equipped weapon, skills, PP, materials, and identified items all persist via JSON

## Requirements

- Python 3.9+
- [Panda3D](https://www.panda3d.org/)
- panda3d-gltf
- panda3d-simplepbr
- tomli
- pman

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| W / A / S / D | Move |
| Space | Wait (skip turn) |
| 1 – 4 | Use skill in slot |
| F | Use first inventory item |
| Z | Drop first inventory item |
| I | Inspect first inventory item |
| E | Save / Forge (in town) · Debug stats (in dungeon) |

## Project Structure

```
main.py              Entry point
game/
  app.py             Main application, input handling, state machine
  save_manager.py    JSON save/load
entities/
  player.py          Player stats, inventory, skills
  enemy.py           Enemy types, AI behaviour
  items.py           Item definitions, rarity/affix system, LootGenerator
  skills.py          Skill definitions and PP system
  status_effects.py  Status effect logic
  entity_base.py     Shared entity base class
systems/
  turn_system.py     Turn resolution, combat, trap/tile effects
  spawn_system.py    Enemy and item placement
world/
  dungeon_generator.py  Procedural room-and-corridor generation
  tilemap.py            Tilemap rendering and theme application
  town_builder.py       Phase 8: load buildings.json, construction helpers
data/
  buildings.json        Phase 8: building costs, prereqs, gold
ui/
  hud.py             In-game HUD (HP, hunger, skills, XP, status)
  item_screen.py     Item inspection overlay
tests/               Unit tests (loot, town building, config, core systems)
```

## Roadmap

Planned phases (see [PLAN.md](PLAN.md) for full detail):

- **Phase 8** – Town building via dungeon materials (Forge upgrades, Herbalist, Inn, Shrine, Guild Hall)
- **Phase 9** – Crafting, cooking, farming, and a daily/seasonal life-sim cycle
- **Phase 10** – Romanceable companions with support-rank system
- **Phase 11** – Monster collecting, Ranch, and evolution system
- **Phase 12** – Infinite dungeon mode, New Game+, final boss arc, multiplayer stub

## License

[MIT](LICENSE.txt)

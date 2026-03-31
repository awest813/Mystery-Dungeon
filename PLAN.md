# Mystery Dungeon – Full Roadmap

---

## ✅ Phase 1 – Core Prototype
Basic Panda3D project, tilemap rendering, player movement, enemy AI placeholder.

## ✅ Phase 2 – Dungeon Generation
Procedural room-and-corridor generation, themed floors (Cave/Ice/Fire), item tiles, stairs.

## ✅ Phase 3 – Resources & Economy
Hunger system, gold drops, XP accumulation, basic save/load (JSON).

## ✅ Phase 4 – Combat & Spawning
Turn-based combat, enemy AI (chase/attack), enemy scaling, spawn system.

## ✅ Phase 5 – Debug & Polish
Smooth camera, hop animation, message log, AI wall-collision fix, recursive-turn fix,
enemy walkability fix, HUD color coding, respawn flow.

## ✅ Phase 6 – Depth Pass (current)
- **Items**: food, potions, weapons, orbs, dungeon keys — weighted per-floor loot tables
- **Level-up system**: XP curve, +HP/+ATK per level, skill learning on level-up
- **Skills / PP system** (PMD-style 4 slots): Slash, Headbutt, Ember, Ice Shard, Thunder,
  Shadow Claw, Giga Impact, Heal, Sleep Powder, Toxic
- **Status effects**: poisoned, burn, confused, paralyzed, asleep
- **Enemy variety**: 8 types with move patterns, status-on-hit, boss dark_knight
- **Dungeon features**: traps, water, lava, sealed boss doors
- **Boss floors** every 5 floors, floor scaling (+12% HP/ATK per floor)
- **Expanded HUD**: skill bar, XP, status, weapon, inventory count, boss alert
- **Save system**: persists inventory, equipped weapon, skills + PP

---

## ✅ Phase 7 – Procedural Loot & Enchantment System

**Goal**: Every weapon found in the dungeon feels unique and worth examining.
Inspired by Diablo 2 item affixes, PMD IQ items, and Chocobo Dungeon cursed/blessed mechanics.

### Implemented
- **Rarity tiers**: Common (grey), Uncommon (green), Rare (blue), Legendary (gold), Cursed (purple)
- **Affix system**: 13 affix tags across 4 categories (offensive, defensive, utility, cursed)
  - Offensive: `keen` (+ATK), `crit` (crit chance), `fiery` (fire dmg + burn), `freezing` (ice dmg + paralyze), `leeching` (life steal %)
  - Defensive: `hardy` (+max HP), `guard` (dmg reduction %), `resist` (status duration -N turns)
  - Utility: `thrifty` (-hunger drain %), `finder` (+gold drop %)
  - Cursed: `leech` (-HP/turn), `fumble` (+confuse chance on move), `volatile` (+warp on hit %)
- **Legendary uniques**: 4 hand-crafted weapons with fixed names, flavour text, and affixes
- **Item identification**: mystery names for non-food items; identified by use, Identify Scroll, or returning to town; persists globally across sessions
- **`LootGenerator.generate()`**: factory with floor-scaled rarity weights
- **Material drops**: 8 enemy types drop materials (slime gel, bat wing, goblin fang, etc.)
- **Player material inventory**: `add_material`, `has_materials`, `spend_materials`, `materials_summary`
- **Town Forge** (tile 8): stand on it + press E to enchant/upgrade equipped weapon using materials
- **Affix effects in combat**: crit, life steal, dmg reduce, hunger save, hp drain, warp on hit, status on hit
- **HUD rarity colour**: equipped weapon slot coloured by rarity tier
- **`ui/item_screen.py`**: item inspection overlay (I key) showing rarity, affixes, flavour text
- **Save/load**: rarity + affixes round-trip via `Item.to_dict/from_dict`; `identified_items` + `materials` persisted
- **48 unit tests** covering all major systems

---

## 🔄 Phase 8 – Town Building Through Dungeon Materials (in progress)

**Goal**: The player's town grows visually and functionally as they bring back materials
farmed in dungeons. Inspired by Recettear, Stardew Valley, and DQ Builders.

### Implemented so far
- **Material nodes** on dungeon floors (`TILE_MATERIAL_NODE`): step on purple deposits for
  theme-weighted materials (Cave / Ice / Fire)
- **Town Plot** north of the square: stand on the green tile and press **E** to cycle
  blueprints; affordable builds spend materials + gold and persist in the save file
- **`data/buildings.json`** + **`world/town_builder.py`**: definitions, prereqs,
  `can_build` / `try_build`, small footprint tiles when certain buildings complete
- **Forge Lv2** blueprint: when built, town forge enchant/upgrade costs are reduced
- **HUD** line for non-zero materials; save field **`completed_buildings`**

### Material Farming
- Enemies drop **materials** on death (Phase 7)
- **Material nodes** (above) supplement enemy drops

### Town Buildings
Long-term targets still include Ranch, Companion Quarters, and full service UIs. Current
`data/buildings.json` uses only **existing** material keys.

| Building | Notes |
|----------|--------|
| **Forge Lv1 / Lv2** | Formal progression; Lv2 lowers forge material costs |
| **Herbalist / Inn / Shrine / Guild** | Placeholder unlocks + footprint tiles; deeper services in later phases |

### Visual Town Growth
- North corridor from the town square; extra floor tiles open when some buildings complete
- Distinct building art and NPCs — still planned

### Material Inventory
- Same stash as Phase 7; HUD shows a compact **Mats:** summary

### Implementation Notes
- `world/town_builder.py`: `BuildingDef`, JSON load, construction helpers
- `game/app.py`: Town Plot, material node harvest, forge tier bonuses
- `data/buildings.json`: requirements and gold costs
- `game/save_manager.py`: `completed_buildings`

---

## 🔜 Phase 9 – Crafting, Cooking & Life Sim

**Goal**: Give the player meaningful things to do between dungeon runs — cook meals for
buffs, craft gear and consumables from gathered materials, tend a garden, and experience
a living daily cycle. Inspired by Stardew Valley, Recettear, and Atelier series.

### Cooking System
- **Kitchen** building (requires 10× Wood, 5× Stone, 3× Herb Bundle) unlocks the cooking interface
- Recipes combine ingredients found in dungeons or grown in the Garden (see below):
  - Raw food items (Oran Berry, Rawst Leaf, Apples, Mushrooms, Monster Drops)
  - **Cooked meals** grant timed buffs lasting the next dungeon run:

| Dish | Ingredients | Buff |
|------|------------|------|
| Hearty Stew | 2× Mushroom, 1× Meat Chunk | +20% max HP for run |
| Ember Curry | 1× Flame Shard, 2× Spice Herb | +15% ATK, immune to Freeze |
| Frost Sorbet | 1× Frost Jewel, 1× Oran Berry | +15% DEF, immune to Burn |
| Revive Broth | 1× Oran Bark, 1× Herb Bundle | Auto-revive once on death |
| Lucky Pudding | 1× Honey, 2× Sweet Herb | +10% gold & item drop rate |
| Stamina Rice | 3× Grain, 1× Herb Bundle | Hunger drains 30% slower |

- Recipes are **discovered** by experimenting (combining unknown ingredients) or found
  as dungeon loot (Recipe Scrolls)
- A **Cookbook** UI tab tracks discovered vs. undiscovered recipes
- Meals expire after one dungeon run; up to 2 meals can be active simultaneously

### Crafting System
- **Workbench** building (requires 8× Wood, 4× Iron Ore) unlocks consumable crafting
- Craft items from dungeon materials without needing to find them as drops:

| Item | Materials | Effect |
|------|-----------|--------|
| Antidote Potion | 2× Herb Bundle, 1× Slime Gel | Cures Poison + Burn |
| Flash Bomb | 1× Flame Shard, 2× Stone | Blinds all enemies in room |
| Escape Rope | 3× Bat Wing, 2× Vine | Instant dungeon exit, keeps loot |
| Spike Trap | 2× Iron Ore, 1× Stone | Placeable trap tile |
| Friend Orb | 1× Monster Core, 2× Moonstone | Guaranteed capture attempt |
| Stamina Seed | 2× Grain, 1× Oran Bark | Permanently +5 max hunger |

- Crafting recipes are unlocked via the Workbench by discovering materials or finding
  **Blueprint** items in dungeons
- Higher-tier Workbench upgrades (Lv2: +10× Steel) unlock advanced recipes

### Farming / Garden
- **Garden Patch** building (requires 5× Wood, 5× Seed Bag) lets the player grow ingredients
- Plant seeds found in dungeons; crops grow over a set number of dungeon runs ("days")
- Crops: Oran Berry (3 days), Herb Bundle (2 days), Sweet Herb (4 days), Grain (2 days)
- Watering (interact with patch before a run) speeds growth by 1 day
- Fully grown crops are harvested automatically on return from the dungeon
- The **Composter** upgrade converts excess crops into Fertilizer, further speeding growth

### Daily / Seasonal Cycle
- Each completed dungeon run advances the in-game **day counter**
- Every 7 days is a new **week**; every 28 days is a new **season** (Spring/Summer/Autumn/Winter)
- Seasonal effects:
  - **Spring**: herb crops grow 1 day faster; monsters drop extra Herb Bundle
  - **Summer**: Flame-type enemies +10% ATK; fire-immune food ingredients spawn more often
  - **Autumn**: gold drops +10%; Lucky Pudding buff doubled
  - **Winter**: Frost-type enemies +10% ATK; hunger drains 20% faster in dungeons
- Seasonal festivals (day 14 & 28 each season) unlock limited-time shop stock and
  special dungeon events

### Life Sim Social Loop
- Each "day" NPCs in town have new dialogue reflecting world events (new building built,
  season change, recent dungeon event)
- Gifting cooked meals to companions (Phase 10) counts as a high-value affection action
- Seasonal festivals allow gift-giving to all town NPCs for small affection/reputation boosts
- **Town Reputation** meter (0–100): raised by building, gifting, and completing bounties;
  unlocks NPC discounts and new dialogue branches

### Implementation Notes
- `world/kitchen.py`: new module, `Recipe` dataclass, cooking interface, meal buff tracker
- `world/workbench.py`: `Blueprint` dataclass, crafting queue, recipe unlock logic
- `world/garden.py`: `Crop` dataclass, growth tick system, harvest logic
- `game/calendar.py`: day/week/season counter, seasonal effect application
- `data/recipes/cooking.json`: all cooking recipes, ingredients, buff definitions
- `data/recipes/crafting.json`: all crafting blueprints, material costs
- `data/crops.json`: crop types, growth times, seasonal modifiers
- `ui/kitchen_screen.py`: recipe browser, cook interface, active meal display
- `ui/workbench_screen.py`: blueprint list, craft interface
- `ui/garden_screen.py`: patch grid, crop status, water/harvest actions
- `game/save_manager.py`: persist meal buffs, crop state, day counter, town reputation

---

## 🔜 Phase 10 – Romanceable Companions

**Goal**: 3–5 unique companions who join the player's party, develop relationships,
and have narrative arcs. Inspired by Persona Q social links, Stardew Valley romance,
and Fire Emblem support conversations.

### Companion Roster (draft)
| Name | Class | Specialty | Personality |
|------|-------|-----------|-------------|
| **Lyra** | Mage | Elemental orbs, long range | Bookish, secretly adventurous |
| **Brom** | Knight | Tanking, adjacent enemy taunt | Gruff but loyal, hates slimes |
| **Mira** | Healer | AOE heal, status cure | Optimistic, collects monster lore |
| **Sable** | Rogue | High crit, trap disarm, steal | Mysterious, dry wit |
| **Finn** | Ranger | Ranged attack, scouting, fog reveal | Earnest, loves rare items |

### Companion Mechanics
- Companions travel the dungeon with the player as AI-controlled allies
- Each occupies a turn slot (move/attack/skill/wait) after the player's turn
- Can be directed with simple commands: Attack/Follow/Hold/Retreat
- Companion HP persists between floors (no full restore — manage carefully)
- If a companion is defeated they retreat to town (not permadeath)

### Relationship System (Persona Q / FE inspired)
- **Affection meter** (0–100) per companion, raised by:
  - Gifting items they like (each companion has preferred item types)
  - Rescuing them when near-death
  - Talking at the Inn (costs one "rest turn")
  - Completing companion-specific dungeon events
- **Support Ranks**: C → B → A → S (romance)
  - Each rank unlocks a cutscene/dialogue event and a passive bonus
  - S-rank: partner ability (unique combined skill usable once per floor)

### Romance Flags
- Each companion has a romance route unlocked at A-rank
- Player chooses to pursue or remain as friends at A-rank conversation
- S-rank romance grants flavor changes: companion calls player by nickname,
  unique color highlight on their HUD portrait, special ending slide

### Implementation Notes
- `entities/companion.py`: `Companion(Entity)` with affection, support_rank, dialogue_key
- `data/companions/lyra.json` etc.: stat profiles, gift preferences, dialogue trees
- `ui/companion_screen.py`: affection display, talk option, gift interface
- `systems/companion_ai.py`: turn resolution for up to 2 active companions
- `game/save_manager.py`: persist affection values, support ranks, romance flags

---

## 🔜 Phase 11 – Monster Collecting

**Goal**: Defeat or befriend dungeon monsters, add them to a roster, deploy them as
dungeon allies or town Ranch residents. Inspired by PMD partner system, Pokemon,
and Digimon Story.

### Capture Mechanics
- After reducing a monster to ≤25% HP, a **Befriend prompt** appears (press B)
- Success chance based on: monster HP%, player level vs monster level, held Friend Orb
- **Friend Orb** (rare item): guarantees capture attempt; consumed on use
- Some monsters can only be befriended with specific items (e.g. Flame Shard for fire_imp)
- Bosses (dark_knight) cannot be captured on first encounter — require clearing the floor
  and returning

### Monster Roster
- Up to **30 captured monsters** stored in the Ranch (built in Phase 8)
- Each captured monster retains: type, name (renameable), level, and affix bonuses
  (if they were a rare/legendary variant — see Phase 7)
- Monsters level up when deployed to the dungeon

### Deployment
- Bring up to **2 monsters** into the dungeon as allies (similar to PMD rescue teams)
- Monsters act on their own turn using their natural AI + learned moves
- Monsters that die in the dungeon lose EXP (not permadeath, but discourages recklessness)

### Monster Evolution / Growth (PMD / Digimon inspired)
- Each monster type has a growth path triggered by level or special item:
  - slime (Lv10 + Slime Crown) → **King Slime** (AOE bounce attack)
  - goblin (Lv12 + War Drum) → **Hobgoblin** (double attack per turn)
  - bat (Lv8 + Moon Wing) → **Vampire Bat** (life steal on hit)
  - ghost (Lv15) → **Wraith** (phase through walls)
  - ice_wisp (Lv12 + Frost Core) → **Blizzard Spirit** (AOE paralyze)
- Evolution changes sprite color, upgrades stats, and unlocks a new skill

### Monster Social Bonds
- Monsters left at the Ranch can interact with companions (see Phase 10)
- High-affinity monster+companion pairs unlock special combo skills in the dungeon

### Ranch Mini-Game
- Monsters at the Ranch passively generate small amounts of their drop material over time
  (e.g. Slime in Ranch → produces Slime Gel each "day" / dungeon run)
- Feeds into the town building material economy (Phase 8)

### Implementation Notes
- `entities/monster_roster.py`: `CapturedMonster` dataclass, roster management
- `systems/capture_system.py`: befriend chance formula, Friend Orb logic
- `data/monsters/evolutions.json`: evolution requirements and stat deltas
- `world/town_builder.py`: Ranch tile interactions, passive material generation
- `ui/ranch_screen.py`: roster view, rename, deploy selection, evolution trigger
- `game/save_manager.py`: persist monster roster, evolution state, Ranch inventory

---

## 🔜 Phase 12 – Integration & Endgame

- **Infinite dungeon mode**: floors 20+ with all systems active, leaderboard score
- **New Game+**: carry forward monster roster and companion bonds; dungeons harder
- **Legendary dungeon events**: rare floor-wide events (blizzard, monster stampede,
  golden floor — all items rare+)
- **Final boss arc**: narrative conclusion using companions and evolved monsters
- **Multiplayer stub**: co-op dungeon runs (2 players, shared loot, split screen)

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

## ✅ Phase 8 – Town Building Through Dungeon Materials

**Goal**: The player's town grows visually and functionally as they bring back materials
farmed in dungeons. Inspired by Recettear, Stardew Valley, and DQ Builders.

### Implemented
- **Material nodes** on dungeon floors (`TILE_MATERIAL_NODE`): step on purple deposits for
  theme-weighted materials (Cave / Ice / Fire)
- **Town Plot** north of the square: stand on the green tile and press **E** to cycle
  blueprints; affordable builds spend materials + gold and persist in the save file
- **`data/buildings.json`** + **`world/town_builder.py`**: definitions, prereqs,
  `can_build` / `try_build`, small footprint tiles when certain buildings complete
- **Forge Lv2** blueprint: when built, town forge enchant/upgrade costs are reduced
- **HUD** line for non-zero materials; save field **`completed_buildings`**
- **Visual building tiles**: each completed building (Herbalist, Inn, Shrine, Guild)
  gets a uniquely colored interactive tile in the north corridor
- **Herbalist Hut** (tile 11): buy potions and food with gold from a cycling shop
- **Inn** (tile 12): rest for a temporary max HP buff that lasts one dungeon run
- **Shrine** (tile 13): purify cursed affixes (50g) or bless weapons with new affixes
  (80g + materials); cycles services on repeated E press
- **Guild Hall** (tile 14): accept bounty quests (kill enemies, clear floors, harvest
  materials) for bonus gold + XP rewards; progress tracked during dungeon runs
- **Bounty tracking**: kill callback in TurnSystem, floor/material tracking in app,
  bounty progress saved/loaded with player data

### Material Farming
- Enemies drop **materials** on death (Phase 7)
- **Material nodes** (above) supplement enemy drops

### Town Buildings

| Building | Services |
|----------|----------|
| **Forge Lv1 / Lv2** | Enchant/upgrade weapons; Lv2 lowers material costs |
| **Herbalist Hut** | Buy potions and food with gold (6 items in rotating stock) |
| **Inn** | Rest for temporary +HP buff (scales with level) |
| **Shrine** | Purify cursed weapons; bless weapons with new affixes |
| **Guild Hall** | Accept bounty quests for bonus gold + XP |

### Visual Town Growth
- North corridor from the town square opens as buildings are completed
- Each building has a distinct colored tile (green, brown, purple, gold)

### Material Inventory
- Same stash as Phase 7; HUD shows a compact **Mats:** summary

### Implementation Notes
- `world/town_builder.py`: `BuildingDef`, JSON load, construction helpers, `_BUILDING_TILE_MAP`
- `game/app.py`: Town Plot, material node harvest, forge tier bonuses, herbalist shop,
  inn rest buff, shrine purify/bless, guild bounty board
- `data/buildings.json`: requirements and gold costs
- `data/shop_stock.json`: herbalist shop item definitions and prices
- `data/bounties.json`: bounty quest definitions (slay, clear, harvest)
- `game/save_manager.py`: `completed_buildings`, `active_bounty`, `inn_buff_hp`

---

## ✅ Phase 9 – Crafting, Cooking & Life Sim

**Goal**: Give the player meaningful things to do between dungeon runs — cook meals for
buffs, craft gear and consumables from gathered materials, tend a garden, and experience
a living daily cycle. Inspired by Stardew Valley, Recettear, and Atelier series.

### Cooking System
- **Kitchen** at Herbalist Hut: press E to cycle between buy/cook modes
- 6 recipes: Hearty Stew (+20% max HP), Ember Curry (+15% ATK, freeze immune),
  Frost Sorbet (+15% DEF, burn immune), Revive Broth (auto-revive), Lucky Pudding (+10% gold),
  Stamina Rice (-30% hunger drain)
- Up to 2 active meal buffs; consumed on dungeon return
- Recipes use dungeon materials (mushroom, meat_chunk, spice_herb, etc.)

### Crafting System
- **Workbench** at Forge: press E to browse and craft from 7 blueprints
- Craft potions, orbs, and consumables from materials without finding them as drops
- Blueprints: Antidote Potion, Flash Bomb, Escape Rope, Heal Salve, Stamina Brew, Spike Kit, Freeze Powder

### Farming / Garden
- **Garden Patch** tile (12,17) in town: press E to cycle plant/water/harvest
- 5 crop types: Oran Berry (3d), Herb Bundle (2d), Sweet Herb (4d), Grain (2d), Mushroom (2d)
- Watering doubles growth speed (2 days per advance instead of 1)
- Season bonus: crops matching current season grow +1 extra day
- 4-plot capacity; harvested items go directly to inventory

### Calendar System
- Day counter advances each time the player returns from a dungeon run
- 4 seasons (Spring/Summer/Autumn/Winter), 28 days each
- Seasonal effects: Spring herbs grow faster, Summer fire enemies stronger,
  Autumn gold bonus, Winter hunger drain increase
- HUD displays current day and season

### Implementation Notes
- `world/kitchen.py`: `CookingRecipe`, `MealBuff`, `load_recipes`, `can_cook`, `cook`
- `world/workbench.py`: `CraftingBlueprint`, `load_blueprints`, `can_craft`, `craft`
- `world/garden.py`: `CropPlot`, `load_crop_definitions`, `get_crop_defs`, `create_plot`, `harvest_plot`, `water_plot`
- `game/calendar.py`: `Calendar`, `SEASONS`, `SEASON_EFFECTS`, day/week/season tracking
- `data/recipes/cooking.json`: 6 cooking recipes with buff definitions
- `data/recipes/crafting.json`: 7 crafting blueprints with material costs
- `data/crops.json`: 5 crop types with growth times and season bonuses
- `game/save_manager.py`: persist `calendar`, `garden_plots`
- `ui/hud.py`: day/season display, active meal buff list
- `entities/items.py`: 10 new ingredient/crafting items
- `game/app.py`: `_herbalist_action` (buy/cook toggle), `_crafting_action`,
  `_garden_action` (plant/water/harvest), `_apply_meal_buffs`, `_advance_garden`
- 22 new tests covering calendar, kitchen, workbench, and garden systems

---

## 🔜 Phase 10 – Romanceable Companions

---

## ✅ Phase 10 – Romanceable Companions

**Goal**: 5 unique companions who join the player's party, develop relationships,
and have narrative arcs. Inspired by Persona Q social links, Stardew Valley romance,
and Fire Emblem support conversations.

### Companion Roster
| Name | Class | Specialty | Personality |
|------|-------|-----------|-------------|
| **Lyra** | Mage | High ATK, ice affinity | Bookish, secretly adventurous |
| **Brom** | Knight | Tank, high HP | Gruff but loyal, hates slimes |
| **Mira** | Healer | Low ATK, supportive | Optimistic, collects monster lore |
| **Sable** | Rogue | High ATK, stealth | Mysterious, dry wit |
| **Finn** | Ranger | Balanced, scouting | Earnest, loves rare items |

### Companion Mechanics
- **Companion tile** in town (purple, position 17,17): press E to deploy/recall
- Up to **2 companions** deployed at once; they follow the player in dungeons
- Companions act on their own turn after enemies (CompanionAI system)
- AI: attacks nearest enemy, moves toward player if no enemies nearby, waits at low HP
- If defeated, companion retreats to town (not permadeath)

### Relationship System
- **Affection meter** (0–100) per companion, raised by:
  - Gifting preferred items (+8), neutral items (+2), disliked items (-3)
  - Talking at the Inn (+3/day, once per day per companion)
  - Duplicate gift penalty (-2 from second gift of same type same day)
- **Support Ranks**: C → B → A → S at thresholds 0/25/55/85 affection
- Romance flag unlocked at S-rank

### Implementation Notes
- `entities/companion.py`: `Companion` class with affection, support_rank, gift/talk/deploy logic
- `data/companions/*.json`: 5 companion definitions with stat profiles and gift preferences
- `systems/companion_ai.py`: `CompanionAI` — turn resolution for deployed companions
- `ui/companion_screen.py`: Companion overlay (C key) showing roster, ranks, affection bars
- `game/save_manager.py`: persist `companions` list and `active_companions` set
- `game/app.py`: companion tile, deploy/recall via E, C key screen, dungeon deployment
- `entities/player.py`: `companions` roster, `active_companions` set
- 4 new tests covering companion data loading and support rank progression

---

## ✅ Phase 11 – Menu System & UI Overhaul

**Goal**: Replace bare-bones HUD with a full menu system: title screen, pause menu,
inventory screen, death screen, and visual health bars. Inspired by Persona Q menus,
PMD screen layout, and Stardew Valley UI polish.

### Menu System
- **Main Menu** (title screen): New Game, Continue (if save exists), Options, Exit
  - Animated title text with shadow, version number, hover effects on buttons
- **Pause Menu** (Escape): Resume, Inventory, Skills, Save, Quit to Title
  - Semi-transparent overlay, hover-highlighted buttons
- **Inventory Screen** (Pause → Inventory): Full item list with selection, description,
  and actions (Use/Equip/Drop)
- **Death Screen**: "DEFEATED" overlay with Rescue (return to town, lose 10% gold + half hunger)
  or Quit to Title
- **Health Bar Widget**: Reusable visual bar component for HP, hunger, XP, etc.

### Input Routing
- Menu state machine: `MENU_NONE`, `MENU_MAIN`, `MENU_PAUSE`, `MENU_INVENTORY`, `MENU_DEATH`
- All gameplay inputs (movement, skills, items, actions) blocked when menu is open
- Escape toggles pause, arrow keys navigate inventory, Enter confirms
- New Game resets player/enemies/companions; Continue loads from save

### Implementation Notes
- `ui/main_menu.py`: `MainMenu` with DirectButton menu items, hover effects, save detection
- `ui/pause_menu.py`: `PauseMenu` with Resume/Inventory/Save/Quit buttons
- `ui/inventory_screen.py`: `InventoryScreen` with item list, detail text, navigation
- `ui/death_screen.py`: `DeathScreen` with rescue penalty and quit options
- `ui/health_bar.py`: `HealthBar` reusable widget with fill frame and label
- `game/app.py`: Menu state machine, input guards, menu callbacks, New Game/Continue flow
- All 86 existing tests pass

---

## 🔜 Phase 12 – Monster Collecting

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

## ✅ Phase 12 – Monster Collecting & Ranch

**Goal**: Defeat or befriend dungeon monsters, add them to a roster, deploy them as
dungeon allies or town Ranch residents. Inspired by PMD partner system, Pokemon,
and Digimon Story.

### Capture Mechanics
- When an enemy drops to ≤25% HP, the player can attempt to befriend them
- Success chance: base 15% + HP bonus (up to +10% at 0 HP) + level diff (+5% per level)
  + Friend Orb (+50%)
- Bosses cannot be captured
- **Friend Orb** (rare dungeon item): guarantees +50% capture chance

### Monster Roster
- Up to **30 captured monsters** stored in the Ranch
- Each monster retains: type, name, level, HP, ATK, XP
- Monsters level up when deployed to the dungeon (+2 HP, +1 ATK per level)

### Evolution System
- 5 evolution paths defined in `data/monsters/evolutions.json`:
  - slime (Lv10 + Slime Crown) → king_slime (+15 HP, +5 ATK)
  - goblin (Lv12 + War Drum) → hobgoblin (+10 HP, +8 ATK)
  - bat (Lv8 + Moon Wing) → vampire_bat (+5 HP, +4 ATK)
  - ghost (Lv15, no item) → wraith (+10 HP, +6 ATK)
  - ice_wisp (Lv12 + Frost Core) → blizzard_spirit (+8 HP, +7 ATK)

### Deployment
- Up to **2 monsters** deployed alongside 2 companions in dungeons
- Monsters act on their own turn using AI (attack nearest, follow player)
- Monsters that die retreat to Ranch (not permadeath)

### Ranch Mini-Game
- Monsters at the Ranch passively generate their drop materials each day
- Feeds into the town building material economy (Phase 8)

### Implementation Notes
- `entities/monster_roster.py`: `CapturedMonster` with XP/leveling/evolution/AI,
  `MonsterRoster` with 30-slot cap, passive material production, full serialization
- `systems/capture_system.py`: `calculate_capture_chance`, `attempt_capture`
- `data/monsters/evolutions.json`: 5 evolution paths with stat bonuses
- `ui/ranch_screen.py`: roster view, deploy toggle, evolution trigger
- `world/dungeon_generator.py` + `world/tilemap.py`: `TILE_RANCH` (cyan)
- `entities/items.py`: Friend Orb, Slime Crown, War Drum, Moon Wing, Frost Core
- `game/save_manager.py`: persist `MonsterRoster` state
- `game/app.py`: Ranch tile placement, RanchScreen integration, deploy/evolve handlers
- 22 new tests covering capture logic, roster management, and evolution triggers

---

## ✅ Phase 13 – Integration & Endgame

**Goal**: Tie all systems together with infinite dungeon scaling, New Game+,
a multi-phase final boss, and legendary random events. Inspired by PMD post-game,
Binding of Isaac endless mode, and roguelike scoring.

### Endless Dungeon (Floor 20+)
- Difficulty scales linearly past floor 20: +8% enemy stats per floor
- **Legendary Events** (10% chance per floor):
  - **Blizzard**: Enemies move slower but deal +20% damage (3 floors)
  - **Golden Floor**: All items rare+, gold doubled (1 floor)
  - **Monster Stampede**: +50% more spawns (2 floors)
  - **Darkness**: Visibility reduced to 3 tiles (2 floors)
  - **Blessing**: Full HP/PP restore (instant)
- High score tracking: `floor × 100 + gold/2 + kills × 10`

### New Game+
- Unlocked after defeating the final boss
- Carries forward: monster roster, companion bonds, materials
- Difficulty multiplier: +25% per NG+ level
- New Game+ button appears on title screen when save exists

### Final Boss: The Abyssal King
- Triggers at floor 25 with a dramatic spawn
- **3 phases** with escalating difficulty:
  - Phase 1: The Guardian (150 HP, 15 ATK, Shadow Claw/Giga Impact)
  - Phase 2: The Fury (100 HP, 20 ATK, adds Toxic/Thunder)
  - Phase 3: The Despair (60 HP, 25 ATK, adds Sleep Powder)
- Visual changes per phase (purple → red → void)
- Victory rewards: 500 gold, 200 XP, Abyssal Crown unique item
- Unlocks NG+ on defeat

### Implementation Notes
- `systems/endless_dungeon.py`: `EndlessDungeon` with scaling, events, high score
- `systems/new_game_plus.py`: `NGPlusState`, `prepare_ngp`, `apply_ngp`
- `entities/boss.py`: `FinalBoss` with multi-phase combat, visual updates
- `data/bosses/final_boss.json`: boss stats, phases, rewards
- `ui/main_menu.py`: Added "New Game+" button
- `game/save_manager.py`: persist `endless_dungeon`, `ngp_state`
- `game/app.py`: boss spawn/defeat flow, NG+ reset, event messages in `next_floor`
- 15 new tests covering endless scaling, events, NG+ state, and boss data

---

## ✅ Phase 15 – Life Sim & Visual Polish

**Goal**: Transform the town into a living world inspired by Story of Seasons and Fantasy Life.
NPCs with daily schedules, a customizable home, seasonal festivals, and PSP/3DS-quality
ambient visuals.

### NPC System
- **4 unique NPCs**: Mayor Elric, Merchant Lina, Blacksmith Grom, Librarian Sage, Farmer Bramble
- **Daily schedules**: Each NPC moves through 5-6 locations throughout the day
- **Gift system**: Preferred (+10), neutral (+3), disliked (-5) gifts; once per day
- **Dialogue trees**: 5+ lines per NPC scaling with affection level
- **Talk/gift interactions**: T key to talk, G key to gift nearby NPCs

### Player Home
- **Furniture placement**: 8 furniture types (bed, table, shelf, rug, lantern, plant, chest, trophy)
- **Grid-based layout** with overlap detection
- **Storage chest**: Extra item and material storage beyond inventory
- **3D interior**: Floor, walls, and furniture rendered as 3D geometry
- **Boss trophy**: Unlocked after defeating the Abyssal King

### Seasonal Festivals
- **6 festivals** across all seasons: Spring Bloom, Summer Fair, Harvest Moon,
  Starlight Night, Snow Festival, New Year's Eve
- **Auto-triggered** on specific calendar days
- **Rewards**: Gold, XP, and unique items
- **Persistent tracking**: Completed festivals saved across runs

### Visual Polish
- **Particle systems**: Fireflies (summer), falling leaves (autumn), snow (winter),
  rain, torch sparks, dust motes — all procedural billboard particles with recycling
- **Post-processing**: Bloom, vignette, color temperature, seasonal color grading
- **Seasonal atmosphere**: Each season gets unique particle + color grade combination

### Controls
- **H**: Enter/exit player house
- **T**: Talk to nearby NPC
- **G**: Gift item to nearby NPC

### Implementation Notes
- `render/particles.py`: `ParticleSystem` with 6 types (Firefly, Leaf, Snow, Rain, Torch, Dust)
- `render/post_process.py`: `PostProcess` with bloom, vignette, seasonal color grading
- `systems/npc_schedule.py`: `NPC` with schedule, dialogue, gift system, 3D model rendering
- `systems/home_system.py`: `HomeSystem` with furniture placement, storage, 3D interior
- `systems/festivals.py`: `FestivalSystem` with 6 seasonal events and reward tracking
- `data/npcs/*.json`: 5 NPC definitions with schedules, gifts, dialogue trees
- `game/app.py`: NPC rendering, schedule updates, festival checks, home/talk/gift handlers
- `game/save_manager.py`: Persist home, festivals, NPC affection
- 25 new tests covering NPCs, home, and festivals

---

## 🔜 Phase 16 – Multiplayer & Online Features

- **Infinite dungeon mode**: floors 20+ with all systems active, leaderboard score
- **New Game+**: carry forward monster roster and companion bonds; dungeons harder
- **Legendary dungeon events**: rare floor-wide events (blizzard, monster stampede,
  golden floor — all items rare+)
- **Final boss arc**: narrative conclusion using companions and evolved monsters
- **Multiplayer stub**: co-op dungeon runs (2 players, shared loot, split screen)

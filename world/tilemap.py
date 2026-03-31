from panda3d.core import NodePath, CardMaker
from world.dungeon_generator import (
    TILE_WALL, TILE_FLOOR, TILE_STAIRS, TILE_ITEM,
    TILE_TRAP, TILE_WATER, TILE_LAVA, TILE_SEALED
)


class TileMap:
    THEMES = {
        "CAVE": {
            "floor":  (0.10, 0.10, 0.15, 1),
            "alt":    (0.12, 0.12, 0.20, 1),
            "water":  (0.10, 0.25, 0.50, 1),
            "lava":   (0.80, 0.20, 0.00, 1),
        },
        "ICE": {
            "floor":  (0.30, 0.40, 0.60, 1),
            "alt":    (0.20, 0.30, 0.50, 1),
            "water":  (0.50, 0.70, 0.90, 1),
            "lava":   (0.80, 0.20, 0.00, 1),
        },
        "FIRE": {
            "floor":  (0.30, 0.10, 0.10, 1),
            "alt":    (0.40, 0.15, 0.10, 1),
            "water":  (0.10, 0.25, 0.50, 1),
            "lava":   (1.00, 0.30, 0.00, 1),
        },
        "TOWN": {
            "floor":  (0.20, 0.20, 0.20, 1),
            "alt":    (0.22, 0.22, 0.22, 1),
            "water":  (0.10, 0.30, 0.60, 1),
            "lava":   (0.80, 0.20, 0.00, 1),
        },
    }

    def __init__(self, width=30, height=30):
        self.width = width
        self.height = height
        self.grid = [[TILE_WALL for _ in range(height)] for _ in range(width)]
        self.root = NodePath("TileMap")
        self.visual_nodes = {}
        self.current_theme = "CAVE"
        # Revealed traps: set of (x,y) that have been stepped on
        self.revealed_traps = set()

    def apply_theme(self, theme_name):
        if theme_name in self.THEMES:
            self.current_theme = theme_name

    def is_in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def set_tile(self, x, y, tile_type):
        if self.is_in_bounds(x, y):
            self.grid[x][y] = tile_type

    def get_tile(self, x, y):
        if self.is_in_bounds(x, y):
            return self.grid[x][y]
        return TILE_WALL

    def is_walkable(self, x, y):
        t = self.get_tile(x, y)
        # SEALED tiles block passage until opened
        return t not in (TILE_WALL, TILE_SEALED)

    def is_stairs(self, x, y):
        return self.get_tile(x, y) == TILE_STAIRS

    def is_item(self, x, y):
        return self.get_tile(x, y) == TILE_ITEM

    def is_trap(self, x, y):
        return self.get_tile(x, y) == TILE_TRAP

    def is_water(self, x, y):
        return self.get_tile(x, y) == TILE_WATER

    def is_lava(self, x, y):
        return self.get_tile(x, y) == TILE_LAVA

    def is_sealed(self, x, y):
        return self.get_tile(x, y) == TILE_SEALED

    def reveal_trap(self, x, y):
        """Called when a trap is stepped on – show it visually."""
        self.revealed_traps.add((x, y))
        node = self.visual_nodes.get((x, y))
        if node:
            node.setColor(0.8, 0.0, 0.8, 1)   # Visible purple trap

    def open_sealed(self, x, y):
        """Unlock a sealed door with a key."""
        if self.is_sealed(x, y):
            self.grid[x][y] = TILE_FLOOR
            node = self.visual_nodes.get((x, y))
            if node:
                theme = self.THEMES[self.current_theme]
                node.setColor(*theme["floor"])

    def setup_visuals(self):
        self.root.getChildren().detach()
        self.visual_nodes = {}
        self.revealed_traps = set()

        cm = CardMaker("floor")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        theme = self.THEMES[self.current_theme]

        for x in range(self.width):
            for y in range(self.height):
                tile_type = self.grid[x][y]
                if tile_type == TILE_WALL:
                    continue

                node = self.root.attachNewNode(cm.generate())
                node.setPos(x, y, 0)
                node.setP(-90)

                if tile_type == TILE_FLOOR:
                    node.setColor(*theme["alt"] if (x + y) % 2 == 0 else theme["floor"])
                elif tile_type == TILE_STAIRS:
                    if self.current_theme == "TOWN":
                        node.setColor(0.0, 0.7, 1.0, 1)
                    else:
                        node.setColor(0.3, 0.9, 0.9, 1)
                elif tile_type == TILE_ITEM:
                    node.setColor(1.0, 0.8, 0.2, 1)   # gold
                elif tile_type == TILE_TRAP:
                    # Traps look like floor until revealed
                    node.setColor(*theme["alt"] if (x + y) % 2 == 0 else theme["floor"])
                elif tile_type == TILE_WATER:
                    node.setColor(*theme["water"])
                elif tile_type == TILE_LAVA:
                    node.setColor(*theme["lava"])
                elif tile_type == TILE_SEALED:
                    node.setColor(0.5, 0.35, 0.1, 1)  # brown sealed door

                self.visual_nodes[(x, y)] = node

    def reparent_to(self, parent):
        self.root.reparentTo(parent)
